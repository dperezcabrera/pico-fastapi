# API Reference

Complete reference documentation for pico-fastapi's public API.

## Module: pico_fastapi

### Decorators

| Decorator | Description |
|-----------|-------------|
| `@controller` | Marks a class as a FastAPI controller |
| `@get(path, **kwargs)` | Defines a GET endpoint |
| `@post(path, **kwargs)` | Defines a POST endpoint |
| `@put(path, **kwargs)` | Defines a PUT endpoint |
| `@delete(path, **kwargs)` | Defines a DELETE endpoint |
| `@patch(path, **kwargs)` | Defines a PATCH endpoint |
| `@websocket(path, **kwargs)` | Defines a WebSocket endpoint |

### Classes

| Class | Description |
|-------|-------------|
| `FastApiConfigurer` | Protocol for application configurers |
| `FastApiSettings` | Configuration dataclass for FastAPI settings |
| `FastApiAppFactory` | Factory that creates FastAPI instances |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `PicoFastAPIError` | Base exception for all pico-fastapi errors |
| `InvalidConfigurerError` | Raised when a configurer doesn't implement the protocol |
| `NoControllersFoundError` | Raised when no controllers are found during startup |

---

## Decorator Reference

### @controller

Marks a class as a FastAPI controller with automatic route registration.

```python
@controller(
    cls: Type = None,
    *,
    scope: str = "request",
    prefix: str = "",
    tags: list[str] = None,
    dependencies: list = None,
    responses: dict = None,
    **kwargs
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | `str` | `"request"` | Component scope (request, websocket, singleton) |
| `prefix` | `str` | `""` | URL prefix for all routes in this controller |
| `tags` | `list[str]` | `None` | OpenAPI tags |
| `dependencies` | `list` | `None` | FastAPI dependencies for all routes |
| `responses` | `dict` | `None` | Default responses for all routes |

**Example:**

```python
@controller(prefix="/users", tags=["Users"], scope="request")
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    @get("/")
    async def list_users(self):
        return self.service.list_all()
```

---

### @get, @post, @put, @delete, @patch

Define HTTP method endpoints on controller methods.

```python
@get(path: str, **kwargs)
@post(path: str, **kwargs)
@put(path: str, **kwargs)
@delete(path: str, **kwargs)
@patch(path: str, **kwargs)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Route path (required) |
| `**kwargs` | | Any FastAPI route parameters |

**Common kwargs:**

| Kwarg | Type | Description |
|-------|------|-------------|
| `response_model` | `Type` | Pydantic model for response |
| `status_code` | `int` | HTTP status code |
| `tags` | `list[str]` | OpenAPI tags |
| `summary` | `str` | OpenAPI summary |
| `description` | `str` | OpenAPI description |
| `deprecated` | `bool` | Mark as deprecated |
| `responses` | `dict` | Additional response documentation |

**Example:**

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

@controller(prefix="/users")
class UserController:
    @get("/", response_model=list[User], tags=["Users"])
    async def list_users(self):
        return [{"id": 1, "name": "Alice"}]

    @post("/", status_code=201, response_model=User)
    async def create_user(self, data: UserCreate):
        return {"id": 1, **data.dict()}

    @delete("/{user_id}", status_code=204)
    async def delete_user(self, user_id: int):
        pass
```

---

### @websocket

Defines a WebSocket endpoint on a controller method.

```python
@websocket(path: str, **kwargs)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | WebSocket route path (required) |
| `**kwargs` | | Any FastAPI WebSocket parameters |

**Example:**

```python
from fastapi import WebSocket

@controller(scope="websocket")
class ChatController:
    def __init__(self, manager: ChatManager):
        self.manager = manager

    @websocket("/ws/chat")
    async def chat(self, websocket: WebSocket):
        await self.manager.handle(websocket)
```

---

## Class Reference

### FastApiConfigurer

Protocol for classes that configure the FastAPI application.

```python
from typing import Protocol, runtime_checkable
from fastapi import FastAPI

@runtime_checkable
class FastApiConfigurer(Protocol):
    @property
    def priority(self) -> int:
        return 0

    def configure(self, app: FastAPI) -> None:
        ...
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `priority` | `int` | `0` | Middleware ordering (negative = outer, non-negative = inner) |

**Methods:**

| Method | Description |
|--------|-------------|
| `configure(app)` | Called to configure the FastAPI application |

**Example:**

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100

    def configure(self, app: FastAPI) -> None:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

---

### FastApiSettings

Dataclass for FastAPI application settings, automatically loaded from configuration.

```python
@configured(target="self", prefix="fastapi", mapping="tree")
@dataclass
class FastApiSettings:
    title: str = "Pico-FastAPI App"
    version: str = "1.0.0"
    debug: bool = False
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `str` | `"Pico-FastAPI App"` | API title (shown in docs) |
| `version` | `str` | `"1.0.0"` | API version |
| `debug` | `bool` | `False` | Debug mode |

**Configuration:**

```yaml
fastapi:
  title: My API
  version: 2.0.0
  debug: true
```

---

### FastApiAppFactory

Factory class that creates FastAPI application instances.

```python
@factory
class FastApiAppFactory:
    @provides(FastAPI, scope="singleton")
    def create_fastapi_app(self, settings: FastApiSettings) -> FastAPI:
        return FastAPI(**dataclasses.asdict(settings))
```

The factory is automatically registered and creates the FastAPI app as a singleton.

---

## Exception Reference

### PicoFastAPIError

Base exception for all pico-fastapi errors.

```python
class PicoFastAPIError(Exception):
    pass
```

**Usage:**

```python
try:
    # pico-fastapi operations
except PicoFastAPIError as e:
    # Handle any pico-fastapi error
```

---

### InvalidConfigurerError

Raised when an object registered as a configurer doesn't implement the required protocol.

```python
class InvalidConfigurerError(PicoFastAPIError):
    def __init__(self, obj: object):
        super().__init__(
            f"Object does not implement FastApiConfigurer.configure(app): {obj!r}"
        )
```

**Cause:** A class is registered as a `FastApiConfigurer` but doesn't have a `configure(app)` method.

**Solution:** Implement the `configure` method:

```python
@component
class MyConfigurer(FastApiConfigurer):
    def configure(self, app: FastAPI) -> None:
        pass  # Add your configuration
```

---

### NoControllersFoundError

Raised when no controllers are registered during application startup.

```python
class NoControllersFoundError(PicoFastAPIError):
    def __init__(self):
        super().__init__(
            "No controllers were registered. "
            "Ensure your controller modules are scanned."
        )
```

**Cause:** No classes decorated with `@controller` were found.

**Solutions:**

1. Add `@controller` decorator to your controller classes
2. Include controller modules in `init(modules=[...])`
3. Check for import errors in controller modules
