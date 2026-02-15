# AI Agent Guidelines

This document provides guidance for AI agents and contributors working on the `py-app-dev` repository.

## Project Overview

**py-app-dev** is a Python library providing application development modules. The codebase follows modern Python practices with strict type checking and comprehensive testing.

- **Package name**: `py-app-dev`
- **Python version**: 3.10+
- **Package manager**: [uv](https://docs.astral.sh/uv/)
- **Build backend**: Poetry
- **CI/CD**: GitHub Actions with semantic-release

## Repository Structure

```
src/py_app_dev/        # Main source code
├── core/              # Core modules (runnable, config, cmd_line, etc.)
└── mvp/               # MVP pattern implementation
tests/                 # Test files (pytest)
docs/                  # Sphinx documentation
examples/              # Example code
```

## Development Workflow

### Quick Start

```bash
# Install pypeline (one-time setup)
pipx install pypeline-runner

# Run the full development pipeline (venv, lint, test, docs)
pypeline run
```

### Running Individual Steps

The `pypeline.yaml` defines the pipeline steps. Run specific steps using:

```bash
# Create/update virtual environment
pypeline run --step CreateVEnv

# Run pre-commit checks (ruff, mypy, codespell)
pypeline run --step PreCommit

# Run tests with coverage
pypeline run --step PyTest

# Build documentation
pypeline run --step Docs

# Run multiple specific steps
pypeline run --step CreateVEnv --step PyTest

# Run with specific Python version
pypeline run --step CreateVEnv --step PyTest --input python_version=3.13
```

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

## Code Quality Rules

> [!IMPORTANT]
> **Follow these professional coding standards in all code.**

1. **Import Placement**: ALL imports MUST be at the top of the file
   - NEVER import modules inside functions or methods
   - Group imports: standard library, third-party, local
   - Use alphabetical ordering within groups
   - This is basic professional Python development

## Non-Negotiable Development Rules

> [!CAUTION]
> **These rules MUST be followed for all code changes. No exceptions.**

### Plan Before Implementation

1. **Always Present a Plan First**: Before making ANY code changes:
   - Present a clear implementation plan describing WHAT will be changed and HOW
   - Wait for explicit user approval before proceeding with implementation
   - Never jump straight to coding, even for seemingly simple changes

2. **Plan Contents Must Include**:
   - Files to be modified/created/deleted
   - Key changes in each file
   - Any design decisions or trade-offs
   - Testing approach

3. **No Exceptions**: Even if the user has already discussed an approach, always confirm the plan before execution. The user must explicitly approve before any code is written.

### Test-First Development

1. **Write Tests Before Implementation**: For any new functionality or bug fix:
   - Write a **meaningful test** that demonstrates the desired behavior or exposes the bug
   - Then implement the code to make the test pass
   - Tests should be **self-explanatory** - clear test names and minimal comments

2. **Quality Over Quantity**:
   - **Less is better**: Write only meaningful tests that add value
   - Avoid redundant or trivial tests that don't catch real issues
   - Each test should verify a specific behavior or edge case
   - Use parametrized tests to cover multiple scenarios efficiently

3. **Test Coverage Philosophy**:
   - Focus on testing **behavior**, not implementation details
   - Critical paths and business logic MUST have tests
   - Trivial getters/setters don't need tests
   - Integration tests for step classes and pipeline interactions

### Validation Requirements

1. **Run Full Pipeline**: After making changes, **ALWAYS** run:

   ```bash
   pypeline run
   ```

   This executes:
   - Virtual environment setup
   - Pre-commit hooks (linting, type checking)
   - All tests
   - Code quality checks

2. **No Shortcuts**: Do not commit code that:
   - Bypasses tests
   - Fails linting or type checking
   - Breaks existing functionality
   - Lacks test coverage for critical functionality

### Definition of Done

1. **Acceptance Criteria**: Changes are NOT complete until:
   - `pypeline run` executes with **zero failures**
   - All pre-commit checks pass
   - New functionality has appropriate test coverage
