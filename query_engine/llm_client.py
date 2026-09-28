"""
CardioGuide LLM Client

Optimized for:
- Qwen3 1.7B
- CPU-based Ollama inference
- Short grounded educational responses
- Low latency
- Predictable output length
- Persistent model warm-up
- Performance diagnostics
"""

from typing import Optional
import os

import requests


class LLMClient:
    """
    Lightweight Ollama client for CardioGuide.

    Configuration:
    - Qwen3 1.7B
    - reasoning disabled
    - bounded context window
    - bounded generation
    - persistent keep-alive
    - explicit request timeout
    """

    def __init__(
        self,
        model: str = "qwen3:1.7b",
        base_url: Optional[str] = None,
        timeout: int = 90,
    ):
        self.model = model

        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")

        self.timeout = timeout
        self.max_output_characters = 6000

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response using Ollama.

        Raises:
            TypeError: invalid prompt type.
            ValueError: empty prompt.
            RuntimeError: Ollama failure or invalid response.
        """

        if not isinstance(prompt, str):
            raise TypeError(
                "Prompt must be a string."
            )

        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        user_prompt = prompt.strip()

        if (
            system_prompt is not None
            and not isinstance(system_prompt, str)
        ):
            raise TypeError(
                "System prompt must be a string or None."
            )

        if system_prompt and system_prompt.strip():
            full_prompt = (
                f"{system_prompt.strip()}\n\n"
                f"{user_prompt}"
            )
        else:
            full_prompt = user_prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "think": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.1,
                "num_ctx": 1536,
                "num_predict": 160,
            },
        }

        print(
            f"[LLM] model={self.model} "
            f"prompt_chars={len(full_prompt)} "
            f"timeout={self.timeout}s",
            flush=True,
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "Could not connect to the local language model service. "
                "Make sure Ollama is running."
            ) from exc

        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "Language model generation timed out after "
                f"{self.timeout} seconds."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            status_code = response.status_code

            raise RuntimeError(
                "Language model service returned HTTP "
                f"status {status_code}."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                "Could not communicate with the local language model service."
            ) from exc

        # ---------------------------------------------------------
        # Parse Ollama response
        # ---------------------------------------------------------

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "Language model service returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Language model service returned an invalid payload."
            )

        # ---------------------------------------------------------
        # Ollama timing diagnostics
        # ---------------------------------------------------------

        def seconds(value):
            if isinstance(value, (int, float)):
                return value / 1_000_000_000
            return 0.0

        load_duration = seconds(
            data.get("load_duration", 0)
        )

        prompt_eval_duration = seconds(
            data.get("prompt_eval_duration", 0)
        )

        eval_duration = seconds(
            data.get("eval_duration", 0)
        )

        total_ollama_time = (
            load_duration
            + prompt_eval_duration
            + eval_duration
        )

        print(
            "\n========== OLLAMA TIMING =========="
        )
        print(
            f"Model:                  {self.model}"
        )
        print(
            f"Load duration:          {load_duration:.2f}s"
        )
        print(
            f"Prompt evaluation:      {prompt_eval_duration:.2f}s"
        )
        print(
            f"Generation:             {eval_duration:.2f}s"
        )
        print(
            f"Total Ollama time:      {total_ollama_time:.2f}s"
        )

        prompt_count = data.get(
            "prompt_eval_count",
            0,
        )

        eval_count = data.get(
            "eval_count",
            0,
        )

        print(
            f"Prompt tokens:          {prompt_count}"
        )

        print(
            f"Generated tokens:       {eval_count}"
        )

        if (
            data.get("eval_duration")
            and eval_count
        ):
            tokens_per_second = (
                eval_count
                / data["eval_duration"]
                * 1_000_000_000
            )

            print(
                f"Generation speed:      "
                f"{tokens_per_second:.2f} tokens/sec"
            )

        if (
            data.get("prompt_eval_duration")
            and prompt_count
        ):
            prompt_tokens_per_second = (
                prompt_count
                / data["prompt_eval_duration"]
                * 1_000_000_000
            )

            print(
                f"Prompt speed:           "
                f"{prompt_tokens_per_second:.2f} tokens/sec"
            )

        print(
            "===================================\n"
        )

        # ---------------------------------------------------------
        # Extract response
        # ---------------------------------------------------------

        content = data.get(
            "response",
            "",
        )

        if not isinstance(content, str):
            raise RuntimeError(
                "Language model service returned an invalid "
                "response body."
            )

        if not content.strip():
            raise RuntimeError(
                "Language model service returned an empty response."
            )

        cleaned = self._clean_response(
            content
        )

        if not cleaned:
            raise RuntimeError(
                "Language model response contained no usable text."
            )

        if len(cleaned) > self.max_output_characters:
            raise RuntimeError(
                "Language model response exceeded the allowed "
                "CardioGuide output size."
            )

        return cleaned

    def _clean_response(
        self,
        text: str,
    ) -> str:
        """
        Remove Qwen reasoning tags defensively.
        """

        if not isinstance(text, str):
            return ""

        cleaned = text.strip()

        if "<think>" in cleaned:
            if "</think>" in cleaned:
                cleaned = (
                    cleaned
                    .split("</think>", 1)[1]
                    .strip()
                )
            else:
                cleaned = (
                    cleaned
                    .replace("<think>", "")
                    .strip()
                )

        return cleaned