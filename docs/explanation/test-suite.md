# Test Suite Package Initialization

This document explains the purpose and usage of the test suite’s package initializer, typically located at `tests/__init__.py`.

## Overview

- What is this?
  - `tests/__init__.py` designates the `tests/` directory as a Python package.
  - It enables relative imports among test modules and optional package-level initialization.
  - In this project, the file is intentionally present and currently empty, which is sufficient to mark `tests/` as a package.

- Why it exists:
  - Without `__init__.py`, test modules cannot use relative imports like `from .helpers import ...`.
  - It provides a central place to optionally expose common utilities or apply lightweight, package-wide test configuration.

## How to Use It

### Keep it minimal
- Prefer keeping `tests/__init__.py` empty unless you have a clear need for package-wide exports or configuration.
- Use `tests/conftest.py` for pytest fixtures and test configuration; pytest will automatically discover fixtures in `conftest.py` without imports.

### Relative imports across tests

With `tests/__init__.py` present, you can organize helpers and use relative imports:

```
tests/
  __init__.py
  helpers/
    __init__.py
    factories.py
  test_user.py
```

In `tests/test_user.py`:

```python
from .helpers.factories import user_factory

def test_user_creation():
    user = user_factory()
    assert user.is_active
```

### Exposing common utilities (optional)

If you want to re-export commonly used utilities so tests can import them from `tests`, you can do so in `tests/__init__.py`:

```python
# tests/__init__.py
from .helpers.factories import user_factory as make_user

__all__ = ["make_user"]
```

Then in a test:

```python
from tests import make_user

def test_user_creation():
    user = make_user()
    assert user.is_active
```

Note:
- This is optional and mainly for convenience.
- Avoid heavy side effects; importing the `tests` package will execute code in `__init__.py`.

### Fixtures: prefer conftest.py

Define pytest fixtures in `tests/conftest.py`, not in `__init__.py`. Pytest will inject them into tests automatically:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def db_session():
    # set up a session
    yield session
    # tear down
```

Use the fixture by naming it in your test function’s parameters:

```python
def test_query(db_session):
    result = db_session.query(...)
    assert result is not None
```

No imports are required to use fixtures defined in `conftest.py`.

### Light package-level configuration (use sparingly)

If you need a small, global tweak that should apply whenever the `tests` package is imported, you can include it in `__init__.py`. For example, turning deprecation warnings into errors to keep the codebase clean:

```python
# tests/__init__.py
import warnings
warnings.simplefilter("error", DeprecationWarning)
```

Be cautious:
- Code in `__init__.py` runs on import of the `tests` package, not automatically during pytest discovery.
- Heavy imports or stateful side effects can slow tests or cause surprises.

## Common Patterns and Pitfalls

- Do:
  - Use `tests/__init__.py` to enable relative imports among tests.
  - Put shared fixtures and pytest configuration in `tests/conftest.py`.
  - Keep `__init__.py` minimal and side-effect free.

- Avoid:
  - Relying on `__init__.py` to “expose” pytest fixtures. Fixtures should be discovered by pytest via `conftest.py`.
  - Adding complex initialization or environment mutations in `__init__.py` that run implicitly when importing `tests`.
  - Circular imports; if you re-export from `__init__.py`, ensure helpers don’t import test modules back.

## Running the Test Suite

- From the repository root, run:
  - `pytest` to execute all tests.
  - `pytest -q` for a quieter run.
  - `pytest tests/path/to/test_file.py::test_case` to run a specific test.

If your tests use relative imports (e.g., `from .helpers import ...`), the presence of `tests/__init__.py` ensures those imports work consistently.