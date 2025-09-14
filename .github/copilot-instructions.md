# Python-App-Dev Development Guide for AI Agents

## Coding Guidelines

- Always include full **type hints** (functions, methods, public attrs, constants).
- Prefer **pythonic** constructs: context managers, `pathlib`, comprehensions when clear, `enumerate`, `zip`, early returns, no over-nesting.
- Follow **SOLID**: single responsibility; prefer composition; program to interfaces (`Protocol`/ABC); inject dependencies.
- **Naming**: descriptive `snake_case` vars/funcs, `PascalCase` classes, `UPPER_SNAKE_CASE` constants. Avoid single-letter identifiers (including `i`, `j`, `a`, `b`) except in tight math helpers.
- Code should be **self-documenting**. Use docstrings only for public APIs or non-obvious rationale/constraints; avoid noisy inline comments.
- Errors: raise specific exceptions; never `except:` bare; add actionable context.
- Imports: no wildcard; group stdlib/third-party/local, keep modules small and cohesive.
- Testability: pure functions where possible; pass dependencies, avoid globals/singletons.
- tests: use `pytest`; keep the tests to a minimum; use parametrized tests when possible; do no add useless comments; the tests shall be self-explanatory.
- pytest fixtures: use them to avoid code duplication; use `conftest.py` for shared fixtures. Use `tmp_path` in case of file system operations.
