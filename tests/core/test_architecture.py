"""Architecture guard tests for the deterministic decision kernel.

These tests are the executable form of the cardinal invariants from
CLAUDE.md: ``src/core`` must stay free of higher/side layers, of any ML
framework, and of nondeterministic randomness. They turn a prose rule into
a mechanical gate, so a regression (human or agent) fails CI instead of
silently eroding the thesis' determinism claim.

The guard is intentionally import-level (plus a light check for aliased
``numpy.random`` usage). It does not try to prove runtime determinism; it
prevents the obvious ways nondeterminism or ML would leak into the kernel.
"""

from __future__ import annotations

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2] / "src" / "core"
REPO_ROOT = CORE_DIR.parents[1]

# Layers the kernel must never depend on (layering + determinism boundary).
FORBIDDEN_LAYERS = (
    "src.explain",
    "src.ui",
    "src.adapters",
    "src.sim",
    "src.ha",
)

# ML/DL frameworks: must never enter the deterministic kernel.
FORBIDDEN_ML = (
    "sklearn",
    "torch",
    "tensorflow",
    "keras",
    "xgboost",
    "lightgbm",
)

# Nondeterministic randomness sources.
FORBIDDEN_RANDOM = (
    "random",
    "numpy.random",
    "secrets",
)

FORBIDDEN_MODULES = FORBIDDEN_LAYERS + FORBIDDEN_ML + FORBIDDEN_RANDOM


def _core_files() -> list[Path]:
    return sorted(CORE_DIR.rglob("*.py"))


def _matches(name: str, forbidden: tuple[str, ...]) -> bool:
    """True if ``name`` equals a forbidden module or is a submodule of one."""
    return any(name == f or name.startswith(f + ".") for f in forbidden)


def _imported_modules(tree: ast.Module) -> list[tuple[str, int]]:
    """Return (module_path, lineno) for every import statement in the tree."""
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # Relative import; cannot reach another top-level layer.
                continue
            module = node.module or ""
            found.append((module, node.lineno))
            for alias in node.names:
                # `from numpy import random` -> treat as `numpy.random`.
                found.append((f"{module}.{alias.name}", node.lineno))
    return found


def _numpy_aliases(tree: ast.Module) -> set[str]:
    """Names that ``numpy`` is bound to (e.g. ``np`` from ``import numpy as np``)."""
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" or alias.name.startswith("numpy."):
                    aliases.add(alias.asname or "numpy")
    return aliases


def _numpy_random_uses(tree: ast.Module, aliases: set[str]) -> list[int]:
    """Line numbers of ``<numpy-alias>.random`` attribute access (e.g. np.random.rand)."""
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "random":
            value = node.value
            if isinstance(value, ast.Name) and value.id in aliases:
                hits.append(node.lineno)
    return hits


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_core_directory_has_python_files() -> None:
    # Guards against a silent regression where the glob finds nothing and the
    # other tests pass vacuously.
    assert _core_files(), f"no python files found under {CORE_DIR}"


def test_core_imports_no_forbidden_modules() -> None:
    violations: list[str] = []
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module, lineno in _imported_modules(tree):
            if _matches(module, FORBIDDEN_MODULES):
                violations.append(
                    f"{_rel(path)}:{lineno} imports forbidden module '{module}'"
                )
    assert not violations, (
        "src/core must stay deterministic and self-contained "
        "(no ML, no randomness, no higher/side layers):\n" + "\n".join(violations)
    )


def test_core_uses_no_numpy_random() -> None:
    violations: list[str] = []
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases = _numpy_aliases(tree)
        for lineno in _numpy_random_uses(tree, aliases):
            violations.append(
                f"{_rel(path)}:{lineno} uses numpy random (nondeterministic)"
            )
    assert not violations, "no nondeterministic randomness in src/core:\n" + "\n".join(
        violations
    )
