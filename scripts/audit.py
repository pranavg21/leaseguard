"""Structural quality audit, run in CI and by the test suite.

Checks that go beyond linting: file and function size, docstrings, test
breadth, unsafe browser APIs, page structure and placeholder text. Run with
``python -m scripts.audit``; it exits non-zero and lists every violation.
"""

import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_LINES = 200
MAX_FUNCTION_LINES = 30
SOURCE_DIRS = ("leaseguard", "scripts")
UNSAFE_JS = re.compile(r"\.innerHTML|\.outerHTML|insertAdjacentHTML|\beval\(|new Function\(|console\.")
TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore")
INLINE_CODE = re.compile(r"<script>|<style|\sstyle=|\son[a-z]+=", re.IGNORECASE)
PLACEHOLDER = re.compile(r"TODO|FIXME|coming soon|lorem ipsum", re.IGNORECASE)


def python_sources() -> Iterator[Path]:
    """Yield every Python source file (not tests)."""
    for folder in SOURCE_DIRS:
        yield from sorted((ROOT / folder).rglob("*.py"))


def web_sources() -> Iterator[Path]:
    """Yield every JavaScript, HTML and CSS file served to browsers."""
    for pattern in ("*.js", "*.html", "*.css"):
        yield from sorted((ROOT / "static").rglob(pattern))


def check_sizes(paths: list[Path]) -> list[str]:
    """Flag files longer than the limit.

    Args:
        paths: Files to check.

    Returns:
        One message per oversized file.
    """
    sizes = {path: len(path.read_text(encoding="utf-8").splitlines()) for path in paths}
    return [f"{p.relative_to(ROOT)}: {n} lines > {MAX_FILE_LINES}" for p, n in sizes.items() if n > MAX_FILE_LINES]


def check_python(path: Path) -> list[str]:
    """Flag long functions, missing docstrings, prints and type-ignore comments.

    Args:
        path: A Python source file.

    Returns:
        Violation messages.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    name = path.relative_to(ROOT)
    problems = [] if ast.get_docstring(tree) else [f"{name}: missing module docstring"]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            problems += _check_definition(node, name)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
            problems.append(f"{name}:{node.lineno}: print() call; use logging")
    if TYPE_IGNORE.search(source):
        problems.append(f"{name}: type-ignore comment")
    return problems


def _check_definition(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, name: Path) -> list[str]:
    problems = []
    length = (node.end_lineno or node.lineno) - node.lineno + 1
    if not isinstance(node, ast.ClassDef) and length > MAX_FUNCTION_LINES:
        problems.append(f"{name}:{node.lineno}: {node.name}() is {length} lines > {MAX_FUNCTION_LINES}")
    if not node.name.startswith("_") and not ast.get_docstring(node):
        problems.append(f"{name}:{node.lineno}: {node.name} has no docstring")
    return problems


def tested_modules() -> set[str]:
    """Return every leaseguard module imported by at least one test."""
    modules: set[str] = set()
    for test in (ROOT / "tests").glob("test_*.py"):
        for node in ast.walk(ast.parse(test.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
                modules.update(f"{node.module}.{alias.name}" for alias in node.names)
            elif isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
    return modules


def check_test_breadth() -> list[str]:
    """Flag Python modules no test imports, and JS files with no matching test.

    Returns:
        Violation messages.
    """
    imported = tested_modules()
    modules = (
        ".".join(path.relative_to(ROOT).with_suffix("").parts).removesuffix(".__init__")
        for path in (ROOT / "leaseguard").rglob("*.py")
    )
    problems = [f"{module}: no test imports this module" for module in modules if module not in imported]
    problems += [
        f"{path.relative_to(ROOT)}: no tests/js/{path.stem}.test.mjs"
        for path in (ROOT / "static").rglob("*.js")
        if not (ROOT / "tests" / "js" / f"{path.stem}.test.mjs").exists()
    ]
    return problems


def check_web(path: Path) -> list[str]:
    """Flag unsafe APIs, placeholder text and HTML structure problems.

    Args:
        path: A file served to browsers.

    Returns:
        Violation messages.
    """
    text = path.read_text(encoding="utf-8")
    name = path.relative_to(ROOT)
    problems = [f"{name}: placeholder text" for _ in PLACEHOLDER.finditer(text)]
    if path.suffix == ".js" and UNSAFE_JS.search(text):
        problems.append(f"{name}: unsafe DOM/eval/console API")
    if path.suffix == ".html":
        if text.count("<h1") != 1:
            problems.append(f"{name}: must contain exactly one <h1>")
        required = ('<html lang="', 'class="skip-link"', 'id="main"', "<title>")
        problems += [f"{name}: missing {marker}" for marker in required if marker not in text]
        if INLINE_CODE.search(text):
            problems.append(f"{name}: inline script, style or event handler")
    return problems


def run_audit() -> list[str]:
    """Run every check.

    Returns:
        All violation messages; empty when the codebase passes.
    """
    python = list(python_sources())
    web = list(web_sources())
    problems = check_sizes(python + web) + check_test_breadth()
    for path in python:
        problems += check_python(path)
    for path in web:
        problems += check_web(path)
    return problems


def main() -> int:
    """Print violations to stderr and return a process exit code."""
    problems = run_audit()
    for problem in problems:
        sys.stderr.write(f"AUDIT: {problem}\n")
    sys.stderr.write(f"Audit {'failed' if problems else 'passed'}: {len(problems)} problem(s)\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
