# Troubleshooting

This guide covers common issues specific to pico-fastapi.
For component-level issues (missing components, circular dependencies, plugin
discovery), see the
[unified pico-boot troubleshooting guide](https://github.com/dperezcabrera/pico-boot/blob/main/docs/troubleshooting.md).

---

## "My routes return 404"

All endpoints return `404 Not Found` even though the controller is defined.

### 1. Is the class decorated with `@controller`?

`@controller` serves two purposes: it registers the class as a `@component`
**and** marks it for route scanning. Without it, pico-fastapi ignores the
class entirely.

```python
from pico_fastapi import controller, get

@controller(prefix="/api")    # required
class UserController:
    @get("/users")
    async def list_users(self):
        return []
```

### 2. Is the controller module in the `modules` list?

```python
container = init(modules=[
    "myapp.controllers",   # must be listed
    "myapp.services",
])
```

> **Common mistake:** listing the package (`"myapp"`) instead of the module.
> `init(modules=["myapp"])` only scans `myapp/__init__.py`. If your
> controllers live in `myapp/controllers.py`, list it explicitly or
> re-export from `__init__.py`.

### 3. Is pico-fastapi loaded?

With `pico-boot`, it is auto-discovered. Without it:

```python
from pico_ioc import init

container = init(modules=[
    "myapp",
    "pico_fastapi.config",      # required
    "pico_fastapi.factory",     # required
])
```

### 4. Does the controller have unsatisfied dependencies?

If `__init__` requires a service that is not registered, the controller
fails to instantiate and its routes are never added. Enable debug logging:

```python
import logging
logging.getLogger("pico_ioc").setLevel(logging.DEBUG)
logging.getLogger("pico_fastapi").setLevel(logging.DEBUG)
```

Look for `ProviderNotFoundError` in the output.

### 5. Is the prefix correct?

```python
@controller(prefix="/api/v2")
class UserController:
    @get("/users")          # full path: /api/v2/users
    async def list_users(self):
        ...
```

The final path is `prefix + route path`. If the client hits `/api/users`
but the prefix is `/api/v2`, you get 404.

---

## `NoControllersFoundError`

```
pico_fastapi.exceptions.NoControllersFoundError:
No controllers were registered. Ensure your controller modules are scanned.
```

This means pico-fastapi's factory found zero `@controller` classes in the
container. Follow the same checklist as "My routes return 404" above.

---

## "My middleware is not running"

### 1. Is the configurer a `@component`?

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer

@component                    # required
class CORSConfigurer(FastApiConfigurer):
    priority = -100

    def configure_app(self, app):
        ...
```

Without `@component`, the container never sees it.

### 2. Does it implement the protocol correctly?

The configurer must have a `configure_app(self, app: FastAPI) -> None` method.
If it doesn't, pico-fastapi discards it silently (v0.2.2+) with a warning:

```
WARNING - Discarding invalid configurer <...>: does not implement FastApiConfigurer protocol
```

### 3. Is the priority correct?

| You want... | Use priority... |
|---|---|
| Middleware that runs before scopes exist (CORS, sessions) | `< 0` (outer) |
| Middleware that can use request-scoped services (auth) | `>= 0` (inner) |

If your auth middleware needs a request-scoped service but has priority
`-50`, it runs **before** `PicoScopeMiddleware` creates the scope and
`container.aget()` will fail.

```
Request -> [Outer: priority < 0] -> [PicoScopeMiddleware] -> [Inner: priority >= 0] -> Handler
```

### 4. Is the configurer module in the `modules` list?

Same rule as controllers: the module must be scanned.

---

## "Request-scoped service is not available"

```
pico_ioc.exceptions.ScopeNotActiveError: Scope 'request' is not active
```

### Cause

You are trying to resolve a request-scoped component outside of an active
request scope. This happens when:

- Middleware with **negative priority** tries to use request-scoped services
  (the scope doesn't exist yet)
- A startup event handler or background task tries to resolve request-scoped
  components

### Fix

1. **Move the middleware to positive priority** so it runs after
   `PicoScopeMiddleware`:

    ```python
    @component
    class AuthConfigurer(FastApiConfigurer):
        priority = 10   # inner — scope is active
    ```

2. **Use `container.get()` (singleton)** instead of `container.aget()`
   (request-scoped) if the service doesn't need request state.

---

## "Session scope not working"

### 1. Is `SessionMiddleware` registered?

Session scope requires Starlette's `SessionMiddleware`. It must be **outer**
(negative priority) so the session is set up before `PicoScopeMiddleware`
reads the session ID:

```python
@component
class SessionConfigurer(FastApiConfigurer):
    priority = -50      # must be negative

    def configure_app(self, app):
        from starlette.middleware.sessions import SessionMiddleware
        app.add_middleware(SessionMiddleware, secret_key="...")
```

### 2. Is the component session-scoped?

```python
@component(scope="session")
class ShoppingCart:
    ...
```

Without `scope="session"`, the component is a singleton and won't vary per
session.

---

## "WebSocket controller doesn't work"

### 1. Does it use `scope="websocket"`?

WebSocket controllers must use websocket scope:

```python
@controller(scope="websocket")    # required for WS
class ChatController:
    @websocket("/ws/chat")
    async def chat(self, ws: WebSocket):
        ...
```

### 2. Does the handler have a `WebSocket` type annotation?

Since v0.1.1, pico-fastapi detects the WebSocket parameter by **type
annotation**, not by name:

```python
# Correct — type annotation present
async def chat(self, ws: WebSocket):
    ...

# Wrong — no annotation, falls back to guessing "websocket"
async def chat(self, ws):
    ...
```

---

## "Configurer runs in the wrong order"

### Same priority is non-deterministic

If two configurers have the same priority, their relative order is not
guaranteed:

```python
@component
class A(FastApiConfigurer):
    priority = 0        # tied with B

@component
class B(FastApiConfigurer):
    priority = 0        # tied with A
```

**Fix:** Use different priorities to enforce order.

### Execution order vs request flow

Configurers are **registered** in priority order (lowest first), but
middleware executes in **reverse registration order** (LIFO stack).
In practice, the priority controls when the middleware **wraps** the
handler in the stack:

```python
# Registration: B (5), then A (10)
# Request flow:  A -> B -> Handler
# Response flow: Handler -> B -> A
```

Use the sandwich diagram for reference:

```
[Outer: -100] -> [Outer: -50] -> [PicoScope] -> [Inner: 0] -> [Inner: 10] -> Handler
```

---

## Return value confusion

### Dicts, tuples, and Response objects

Controllers can return several types. pico-fastapi normalizes them:

| Return type | Behavior |
|---|---|
| `dict`, `list`, `str`, `int` | `JSONResponse` with status 200 |
| `(content, status_code)` | `JSONResponse` with given status |
| `(content, status_code, headers)` | `JSONResponse` with status + headers |
| `Response` / `JSONResponse` | Passed through as-is |

```python
@get("/items/{id}")
async def get_item(self, id: int):
    item = self.service.find(id)
    if item is None:
        return {"error": "Not found"}, 404   # tuple form
    return item                               # dict form -> 200
```

---

## Debugging tips

### Enable logging for the full stack

```python
import logging

logging.getLogger("pico_ioc").setLevel(logging.DEBUG)
logging.getLogger("pico_boot").setLevel(logging.DEBUG)
logging.getLogger("pico_fastapi").setLevel(logging.DEBUG)
```

### Inspect registered controllers

After `init()`, you can inspect the container to see what controllers were
discovered:

```python
from fastapi import FastAPI

app = container.get(FastAPI)
for route in app.routes:
    if hasattr(route, "methods"):
        print(f"{route.methods} {route.path}")
```

### Inspect registered middleware

```python
for m in app.user_middleware:
    print(f"{m.cls.__name__} (kwargs={m.kwargs})")
```

---

## See also

- [Unified troubleshooting guide](https://github.com/dperezcabrera/pico-boot/blob/main/docs/troubleshooting.md) — covers component discovery, circular dependencies, configuration, and more
- [FAQ](./faq.md) — common questions
- [Configurers guide](./user-guide/configurers.md) — middleware ordering in depth
