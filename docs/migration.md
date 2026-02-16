# Migration Guide

This document describes breaking changes and migration steps between pico-fastapi versions.

---

## v0.2.1 to v0.2.2

**Release date:** 2026-02-06

### InvalidConfigurerError removed

The `InvalidConfigurerError` exception class was **removed** in v0.2.2.
Invalid configurers are now logged as a warning and silently discarded instead of raising an exception.

#### Before (v0.2.1)

```python
from pico_fastapi import InvalidConfigurerError

# Application code that caught the error
try:
    container = init(modules=["myapp"])
    app = container.get(FastAPI)
except InvalidConfigurerError as e:
    print(f"Bad configurer: {e}")
```

```python
# Import that existed in v0.2.1
from pico_fastapi.exceptions import InvalidConfigurerError
```

#### After (v0.2.2+)

```python
# InvalidConfigurerError no longer exists.
# Remove all imports and except clauses referencing it.

# Instead, check your logs for warnings:
#   WARNING - Discarding invalid configurer <...>: does not implement FastApiConfigurer protocol

# If you need to detect invalid configurers programmatically,
# catch PicoFastAPIError (the base class) or check logs:
import logging

logging.getLogger("pico_fastapi.factory").setLevel(logging.WARNING)
```

#### What to change

1. **Remove all imports** of `InvalidConfigurerError`.
2. **Remove all `except InvalidConfigurerError`** clauses.
3. Replace with `PicoFastAPIError` if you need a catch-all, or rely on log output.
4. If you had tests asserting `InvalidConfigurerError` was raised, update them to verify that a warning is logged and the invalid configurer is skipped.

#### Verifying the migration

```python
# Test that invalid configurers produce a warning, not an exception
import logging

def test_invalid_configurer_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="pico_fastapi.factory"):
        # Bootstrap with an object that doesn't implement FastApiConfigurer
        container = init(modules=["myapp"])
        app = container.get(FastAPI)

    assert "Discarding invalid configurer" in caplog.text
```

---

## v0.1.2 to v0.2.0

**Release date:** 2025-11-25

### pico-boot auto-discovery added

No breaking changes.  `pico-fastapi` is now automatically discovered via the `pico_boot.modules` entry point when using `pico-boot`.

If you were previously including `"pico_fastapi"` explicitly in your modules list with `pico-boot`, you can remove it:

#### Before

```python
from pico_boot import init

container = init(modules=[
    "myapp",
    "pico_fastapi",  # No longer needed with pico-boot
])
```

#### After

```python
from pico_boot import init

container = init(modules=["myapp"])
# pico-fastapi is auto-discovered
```

If you are using `pico_ioc.init()` directly (without pico-boot), you still need to include the pico-fastapi modules explicitly.

---

## v0.1.1 to v0.1.2

**Release date:** 2025-11-18

### Middleware ordering fix (Sandwich strategy)

The `PicoScopeMiddleware` was previously always added as the outermost middleware, which prevented inner middlewares (like authentication) from accessing the IoC container.

v0.1.2 introduced the **Sandwich strategy**: configurers with `priority < 0` wrap the scope middleware (outer), while configurers with `priority >= 0` run inside the scope (inner).

#### Before (v0.1.1)

All configurers ran before `PicoScopeMiddleware`, regardless of priority.  Auth middleware could not access request-scoped services.

#### After (v0.1.2+)

```python
@component
class AuthConfigurer(FastApiConfigurer):
    priority = 10  # Inner: runs AFTER PicoScopeMiddleware

    def configure(self, app: FastAPI) -> None:
        # This middleware can now access request-scoped services
        app.add_middleware(AuthMiddleware)


@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Outer: runs BEFORE PicoScopeMiddleware

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

#### What to change

Review your configurers and assign appropriate priorities:

- CORS, session, rate-limiting: use negative priority (e.g. `-100`, `-50`, `-10`)
- Auth, logging, business-logic hooks: use non-negative priority (e.g. `0`, `10`)

---

## v0.1.0 to v0.1.1

**Release date:** 2025-11-18

### Memory leak fix

Request and WebSocket scopes are now explicitly cleaned up after connection closure.  No code changes needed -- update the dependency.

### WebSocket parameter detection change

WebSocket parameters are now detected by **type annotation** instead of argument name.

#### Before (v0.1.0)

```python
# Only worked if the parameter was named exactly "websocket"
@websocket("/ws")
async def handle(self, websocket):
    await websocket.accept()
```

#### After (v0.1.1+)

```python
from fastapi import WebSocket

# Any parameter name works, as long as it has the WebSocket annotation
@websocket("/ws")
async def handle(self, ws: WebSocket):
    await ws.accept()
```

### Controller discovery change

Controllers are no longer tracked in a global `CONTROLLERS` set.  They are discovered by inspecting the pico-ioc container's metadata directly.  This fixes state pollution issues during testing.

No code changes needed unless you were relying on the internal `CONTROLLERS` set.

---

## Summary Table

| Version | Key Change | Action Required |
|---------|-----------|-----------------|
| v0.2.2 | `InvalidConfigurerError` removed | Remove imports and except clauses |
| v0.2.0 | pico-boot auto-discovery | Remove explicit `"pico_fastapi"` from modules (optional) |
| v0.1.2 | Sandwich middleware ordering | Review configurer priorities |
| v0.1.1 | WebSocket annotation detection | Add `WebSocket` type hint to WS parameters |
| v0.1.1 | Memory leak fix | Update dependency |
