# Exceptions

This reference documents the custom exception classes provided by pico-fastapi. These exceptions signal failures during application startup, and they allow you to handle these conditions explicitly in your code.

## Overview

- `PicoFastAPIError` is the common base class for all custom errors in pico-fastapi.
- `NoControllersFoundError` is raised when the controller discovery process completes without finding any controllers.

Catching the base class lets you handle all pico-fastapi-specific errors in one place.

Typical import:

```python
from pico_fastapi.exceptions import (
    PicoFastAPIError,
    NoControllersFoundError,
)
```

## PicoFastAPIError

Base class for all pico-fastapi exceptions.

- Use this to catch any pico-fastapi-specific error without matching a concrete subclass.
- When writing library or application code on top of pico-fastapi, prefer catching `PicoFastAPIError` instead of broad exceptions like `Exception`, to avoid masking unrelated errors.

Example:

```python
try:
    bootstrap_app()
except PicoFastAPIError as exc:
    # Handle configuration or discovery errors uniformly
    logger.error(f"pico_fastapi startup failed: {exc}")
    raise
```

## NoControllersFoundError

Raised when the system cannot find any controllers during discovery.

**Exact message:**
```
No controllers were registered. Ensure your controller modules are scanned.
```

Constructor signature:
- `NoControllersFoundError()` (takes no arguments)

When raised:
- By `register_controllers()` after scanning the container for controllers and finding none.

Example usage during discovery:

```python
from pico_fastapi.exceptions import NoControllersFoundError

try:
    register_controllers(app, container)
except NoControllersFoundError:
    logger.warning("No controllers found; the API will expose no endpoints.")
```

## Removed Exceptions

### InvalidConfigurerError (removed in v0.2.2)

`InvalidConfigurerError` was removed in v0.2.2. Invalid configurers are now logged as a warning and silently discarded. See the [Migration Guide](../migration.md) for details.

## Recommendations

- Catch `PicoFastAPIError` at application boundaries (e.g., startup) to handle all pico-fastapi-specific failures in a single place.
- Do not rely on the exact exception message in code paths; match on the exception class to make your code resilient to message changes.

---

## Auto-generated API

::: pico_fastapi.exceptions
