import ast
from pathlib import Path


FILES = [
    "query_engine/evidence_builder.py",
    "query_engine/research_query_builder.py",
    "query_engine/source_processor.py",
    "query_engine/web_searcher.py",
    "query_engine/response_planner.py",
    "query_engine/response_generator.py",
]


def inspect_file(file_path: str) -> None:
    print("\n" + "=" * 100)
    print(f"FILE: {file_path}")
    print("=" * 100)

    path = Path(file_path)

    if not path.exists():
        print("ERROR: File does not exist")
        return

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        print(f"ERROR PARSING FILE: {type(exc).__name__}: {exc}")
        return

    print(f"LINES: {len(source.splitlines())}")

    # ------------------------------------------------------------------
    # IMPORTS
    # ------------------------------------------------------------------
    print("\n--- IMPORTS ---")

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                print(f"import {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            print(f"from {module} import {names}")

    # ------------------------------------------------------------------
    # CLASSES
    # ------------------------------------------------------------------
    print("\n--- CLASSES ---")

    found_class = False

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        found_class = True

        print(f"\nCLASS: {node.name}")

        if node.bases:
            bases = ", ".join(ast.unparse(base) for base in node.bases)
            print(f"  BASES: {bases}")

        for item in node.body:

            # Dataclass / class-level assignments
            if isinstance(item, ast.AnnAssign):
                target = ast.unparse(item.target)
                annotation = ast.unparse(item.annotation)

                if item.value is not None:
                    value = ast.unparse(item.value)
                    print(f"  FIELD: {target}: {annotation} = {value}")
                else:
                    print(f"  FIELD: {target}: {annotation}")

            elif isinstance(item, ast.Assign):
                targets = ", ".join(ast.unparse(t) for t in item.targets)

                try:
                    value = ast.unparse(item.value)
                except Exception:
                    value = "..."

                print(f"  CLASS ATTRIBUTE: {targets} = {value}")

            # Methods
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                print_method(item, indent="  ")

    if not found_class:
        print("  NONE")

    # ------------------------------------------------------------------
    # MODULE-LEVEL FUNCTIONS
    # ------------------------------------------------------------------
    print("\n--- MODULE-LEVEL FUNCTIONS ---")

    found_function = False

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found_function = True
            print_method(node, indent="")

    if not found_function:
        print("NONE")


def print_method(node, indent: str = "") -> None:
    """Print a useful summary of a function/method."""

    kind = "async " if isinstance(node, ast.AsyncFunctionDef) else ""

    arguments = []

    # Positional / normal arguments
    for arg in node.args.args:
        annotation = ""

        if arg.annotation is not None:
            annotation = f": {ast.unparse(arg.annotation)}"

        arguments.append(f"{arg.arg}{annotation}")

    # *args
    if node.args.vararg:
        arg = node.args.vararg
        annotation = ""

        if arg.annotation is not None:
            annotation = f": {ast.unparse(arg.annotation)}"

        arguments.append(f"*{arg.arg}{annotation}")

    # Keyword-only arguments
    for arg in node.args.kwonlyargs:
        annotation = ""

        if arg.annotation is not None:
            annotation = f": {ast.unparse(arg.annotation)}"

        arguments.append(f"{arg.arg}{annotation}")

    # **kwargs
    if node.args.kwarg:
        arg = node.args.kwarg
        annotation = ""

        if arg.annotation is not None:
            annotation = f": {ast.unparse(arg.annotation)}"

        arguments.append(f"**{arg.arg}{annotation}")

    signature = ", ".join(arguments)

    # Return annotation
    if node.returns is not None:
        return_type = ast.unparse(node.returns)
        return_text = f" -> {return_type}"
    else:
        return_text = ""

    print(
        f"{indent}{kind}{node.name}"
        f"({signature})"
        f"{return_text}"
    )

    # --------------------------------------------------------------
    # Method decorators
    # --------------------------------------------------------------
    if node.decorator_list:
        decorators = []

        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))

        print(
            f"{indent}  DECORATORS: "
            + ", ".join(decorators)
        )

    # --------------------------------------------------------------
    # Method docstring
    # --------------------------------------------------------------
    docstring = ast.get_docstring(node)

    if docstring:
        first_line = docstring.strip().splitlines()[0]
        print(f'{indent}  DOCSTRING: "{first_line}"')

    # --------------------------------------------------------------
    # Direct calls made inside the method
    # --------------------------------------------------------------
    calls = []

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            try:
                call_name = ast.unparse(child.func)
                calls.append(call_name)
            except Exception:
                pass

    if calls:
        unique_calls = []

        for call in calls:
            if call not in unique_calls:
                unique_calls.append(call)

        print(
            f"{indent}  CALLS: "
            + ", ".join(unique_calls[:30])
        )


def main() -> None:
    print("=" * 100)
    print("CARDIOGUIDE RAG COMPONENT INSPECTOR")
    print("=" * 100)
    print("Purpose: inspect existing RAG interfaces before repairing them.")
    print("This script does NOT modify any project files.")

    for file_path in FILES:
        inspect_file(file_path)

    print("\n" + "=" * 100)
    print("INSPECTION COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()