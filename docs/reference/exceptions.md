# Exceptions

This reference documents the custom exception classes provided by the pico_fastapi project. These exceptions are used to signal failures in application configuration and in controller discovery, and they allow you to handle these conditions explicitly in your code.

## Overview

- PicoFastAPIError is the common base class for all custom errors in pico_fastapi.
- NoControllersFoundError is raised when the controller discovery process completes without finding any controllers.

Catching the base class lets you handle all pico_fastapi-specific errors in one place. Catching the specific subclasses lets you handle configuration vs. discovery failures differently.

Typical import:

```python
from pico_fastapi.exceptions import (
    PicoFastAPIError,
    InvalidConfigurerError,
    NoControllersFoundError,
)
```

## PicoFastAPIError

Base class for all pico_fastapi exceptions.

- Use this to catch any pico_fastapi-specific error without matching a concrete subclass.
- When writing library or application code on top of pico_fastapi, prefer catching PicoFastAPIError instead of broad exceptions like Exception, to avoid masking unrelated errors.

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

Constructor signature:
- NoControllersFoundError()

When to raise:
- After scanning designated modules or packages for controllers and no eligible controllers are found.

Example usage during discovery:

```python
from pico_fastapi.exceptions import NoControllersFoundError

def discover_and_register_controllers(package: str):
    controllers = discover_controllers(package=package)  # project-specific function
    if not controllers:
        raise NoControllersFoundError()

    for controller in controllers:
        register_controller(controller)
```

Example handling:

```python
try:
    discover_and_register_controllers("app.controllers")
except NoControllersFoundError:
    # Decide how to handle an empty application
    logger.warning("No controllers found; the API will expose no endpoints.")
    # You may halt startup or continue with limited functionality
```

## Recommendations

- Prefer raising InvalidConfigurerError and NoControllersFoundError for configuration and discovery issues instead of generic errors like ValueError or RuntimeError. This makes error handling clearer and more robust.
- Catch PicoFastAPIError at application boundaries (e.g., startup) to handle all pico_fastapi-specific failures in a single place.
- Do not rely on the exact exception message in code paths; match on the exception class to make your code resilient to message changes.