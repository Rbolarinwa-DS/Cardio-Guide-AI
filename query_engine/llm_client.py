"""
CardioGuide LLM Client

Provider: OpenRouter
Default model: Qwen3.8 27B (free)

Design goals:
- Short, grounded, controlled-length responses.
- Reasoning suppressed at the request level (not just cleaned up after).
- Optional strict JSON mode for callers that need parseable output
  (e.g. a normalizer or structured-extraction path), without forcing
  every caller into JSON mode.
- Consistent token/character limits (no dead safety checks).
- Bounded retry on transient failures (429 / 5xx) with backoff.
- Defensive <think> stripping as a backstop, not the primary control.
- Clear, typed failure modes the caller can catch and fall back on.
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_THINK_OPEN_RE = re.compile(r"<think>", re.IGNORECASE)

# Status codes worth retrying: rate limit + common transient server errors.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class LLMResult:
    """Everything about a generation worth inspecting, not just the text."""
    text: str
    finish_reason: Optional[str]
    truncated: bool
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    had_think_leak: bool  # True if reasoning tags survived to the raw output


class LLMClient:
    """
    Lightweight OpenRouter client for CardioGuide.

    Raises:
        RuntimeError   — configuration problems, provider failures, or a
                          response that fails validation. Safe for the
                          caller to catch broadly and fall back.
        TypeError / ValueError — bad input from the caller (programmer
                          error), not a provider failure. Not meant to be
                          silently swallowed.
    """

    def __init__(
        self,
        model: str = "qwen/qwen3.8-27b:free",
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 2,
        max_output_tokens: int = 600,
        max_output_characters: int = 4000,
        verbose: bool = True,
    ):
        self.model = model
        self.base_url = (
            base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose

        # Keep the token cap and character cap in the same ballpark so
        # the character check can actually fire. ~4 chars/token is a
        # reasonable English-language estimate; not exact, just sane.
        self.max_output_tokens = max_output_tokens
        self.max_output_characters = max_output_characters

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[LLMClient] {message}", flush=True)

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Generate a response and return the cleaned text.

        json_mode=True asks the provider to constrain output to a JSON
        object (via response_format). Only set this for callers that
        actually parse JSON — forcing it on free-text answers can
        distort normal prose responses.

        For full diagnostics (finish_reason, token counts, whether a
        think-tag leaked through), use generate_detailed() instead.
        """
        result = self.generate_detailed(
            prompt,
            system_prompt=system_prompt,
            json_mode=json_mode,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return result.text

    def generate_detailed(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
    ) -> LLMResult:
        self._validate_config()
        user_prompt = self._validate_prompt(prompt, system_prompt)

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_output_tokens,
            # Unified OpenRouter reasoning control. "effort": "none" asks
            # the model not to reason; "exclude": True additionally tells
            # OpenRouter not to return reasoning tokens even if the model
            # produces them anyway. Both are set because per-model
            # support for "effort" varies, while "exclude" is documented
            # as universally supported.
            "reasoning": {"effort": "none", "exclude": True},
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = self._build_headers()

        self._log(
            f"model={self.model} prompt_chars={len(user_prompt)} "
            f"json_mode={json_mode} timeout={self.timeout}s"
        )

        data, elapsed = self._request_with_retry(headers, payload)
        return self._parse_response(data, elapsed)

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_config(self) -> None:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    def _validate_prompt(self, prompt: str, system_prompt: Optional[str]) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        if system_prompt is not None and not isinstance(system_prompt, str):
            raise TypeError("System prompt must be a string or None.")
        return prompt.strip()

    def _build_headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        http_referer = os.getenv("OPENROUTER_HTTP_REFERER")
        x_title = os.getenv("OPENROUTER_X_TITLE", "CardioGuide AI")
        if http_referer:
            headers["HTTP-Referer"] = http_referer
        if x_title:
            headers["X-Title"] = x_title
        return headers

    # =========================================================
    # REQUEST / RETRY
    # =========================================================

    def _request_with_retry(self, headers: dict, payload: dict) -> tuple[dict, float]:
        """
        POST with bounded retry on rate limits and transient server
        errors. Retries use exponential backoff and honor a
        Retry-After header when the provider sends one.
        """
        last_exc: Optional[Exception] = None
        attempt_start = time.perf_counter()

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.exceptions.ConnectionError as exc:
                last_exc = RuntimeError("Could not connect to OpenRouter.")
                last_exc.__cause__ = exc
            except requests.exceptions.Timeout as exc:
                last_exc = RuntimeError(
                    f"Language model generation timed out after {self.timeout}s."
                )
                last_exc.__cause__ = exc
            except requests.exceptions.RequestException as exc:
                last_exc = RuntimeError("Could not communicate with OpenRouter.")
                last_exc.__cause__ = exc
            else:
                if response.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                    wait = self._retry_delay(response, attempt)
                    self._log(
                        f"HTTP {response.status_code} from OpenRouter, "
                        f"retrying in {wait:.1f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait)
                    continue

                elapsed = time.perf_counter() - attempt_start
                self._raise_for_status(response)
                return self._safe_json(response), elapsed

            if attempt < self.max_retries:
                wait = 2 ** attempt
                self._log(f"{last_exc}. Retrying in {wait}s.")
                time.sleep(wait)
                continue
            raise last_exc

        # Unreachable in practice, but keeps type-checkers happy.
        raise RuntimeError("Exhausted retries without a response.")

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(float(retry_after), 0.5)
            except ValueError:
                pass
        return float(2 ** attempt)

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.ok:
            return

        status_code = response.status_code
        error_data = self._safe_json(response, allow_empty=True)
        error_message = ""

        if isinstance(error_data, dict):
            error_object = error_data.get("error")
            if isinstance(error_object, dict):
                error_message = str(error_object.get("message", ""))
            elif error_object:
                error_message = str(error_object)

        if error_message:
            raise RuntimeError(f"OpenRouter returned HTTP {status_code}: {error_message}")
        raise RuntimeError(f"OpenRouter returned HTTP {status_code}.")

    @staticmethod
    def _safe_json(response: requests.Response, allow_empty: bool = False) -> dict:
        try:
            data = response.json()
        except ValueError as exc:
            if allow_empty:
                return {}
            raise RuntimeError("OpenRouter returned invalid JSON.") from exc
        if not isinstance(data, dict):
            if allow_empty:
                return {}
            raise RuntimeError("OpenRouter returned an invalid payload.")
        return data

    # =========================================================
    # RESPONSE PARSING
    # =========================================================

    def _parse_response(self, data: dict, elapsed: float) -> LLMResult:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenRouter returned no completion choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise RuntimeError("OpenRouter returned an invalid completion choice.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("OpenRouter returned an invalid message.")

        content = message.get("content", "")
        if not isinstance(content, str):
            raise RuntimeError("OpenRouter returned an invalid response body.")
        if not content.strip():
            raise RuntimeError("OpenRouter returned an empty response.")

        finish_reason = first_choice.get("finish_reason")
        truncated = finish_reason == "length"

        had_think_leak = bool(_THINK_BLOCK_RE.search(content)) or bool(
            _THINK_OPEN_RE.search(content)
        )
        cleaned = self._clean_response(content)

        if not cleaned:
            raise RuntimeError("Language model response contained no usable text.")
        if len(cleaned) > self.max_output_characters:
            raise RuntimeError(
                "Language model response exceeded the allowed CardioGuide output size "
                f"({len(cleaned)} > {self.max_output_characters} chars)."
            )

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0)) if isinstance(usage, dict) else 0
        completion_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0)) if isinstance(usage, dict) else 0
        total_tokens = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0

        self._log(
            f"latency={elapsed:.2f}s finish_reason={finish_reason} "
            f"think_leak={had_think_leak} "
            f"tokens(prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens})"
        )
        if truncated:
            self._log(
                "WARNING: response truncated by max_tokens (finish_reason=length). "
                "Content may be cut off mid-sentence."
            )
        if had_think_leak:
            self._log(
                "WARNING: reasoning tags leaked into content despite reasoning.exclude=True; "
                "stripped defensively."
            )

        return LLMResult(
            text=cleaned,
            finish_reason=finish_reason,
            truncated=truncated,
            latency_s=elapsed,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            had_think_leak=had_think_leak,
        )

    @staticmethod
    def _clean_response(text: str) -> str:
        """Strip <think>...</think> blocks defensively (backstop, not primary control)."""
        if not isinstance(text, str):
            return ""

        cleaned = _THINK_BLOCK_RE.sub("", text)

        # Handle an unterminated <think> (truncated mid-reasoning): drop
        # everything from the open tag onward rather than leaving a
        # dangling tag in the output.
        open_match = _THINK_OPEN_RE.search(cleaned)
        if open_match:
            cleaned = cleaned[: open_match.start()]

        return cleaned.strip()