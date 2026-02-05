# Pico-FastAPI Documentation

`pico-fastapi` is a seamless integration layer between **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** and **[FastAPI](https://fastapi.tiangolo.com/)**, bringing true inversion of control and constructor-based dependency injection to FastAPI applications.

---

## Quick Install

```bash
pip install pico-fastapi
```

For auto-discovery with pico-boot:

```bash
pip install pico-boot pico-fastapi
```

---

## 30-Second Example

```python
from pico_ioc import component
from pico_fastapi import controller, get

@component
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

@controller(prefix="/api")
class GreetingController:
    def __init__(self, service: GreetingService):
        self.service = service

    @get("/greet/{name}")
    async def greet(self, name: str):
        return {"message": self.service.greet(name)}
```

```python
from pico_boot import init
from fastapi import FastAPI

container = init(modules=["myapp"])
app = container.get(FastAPI)
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Controller Classes** | Spring-style `@controller` decorator with route methods |
| **Constructor Injection** | Dependencies injected via `__init__`, not function parameters |
| **Request Scopes** | Automatic request, session, and websocket scope management |
| **Configurer Pattern** | Pluggable middleware configuration with priority ordering |
| **Zero Config** | Auto-discovered when using pico-boot |

---

## Documentation Structure

| # | Section | Description | Link |
|---|---------|-------------|------|
| 1 | **Getting Started** | 5-minute tutorial | [getting-started.md](./getting-started.md) |
| 2 | **Tutorial** | Step-by-step guide | [tutorial.md](./tutorial.md) |
| 3 | **User Guide** | Core concepts and patterns | [user-guide/](./user-guide/index.md) |
| 4 | **How-To Guides** | Practical examples | [how-to/](./how-to/index.md) |
| 5 | **Architecture** | Design and internals | [architecture.md](./architecture.md) |
| 6 | **API Reference** | Decorators, classes, exceptions | [reference/](./reference/index.md) |
| 7 | **FAQ** | Common questions | [faq.md](./faq.md) |

---

## Core APIs at a Glance

### Controllers

```python
from pico_fastapi import controller, get, post, put, delete, patch

@controller(prefix="/users", tags=["Users"])
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    @get("/")
    async def list_users(self):
        return self.service.get_all()

    @post("/")
    async def create_user(self, data: UserCreate):
        return self.service.create(data)

    @get("/{user_id}")
    async def get_user(self, user_id: int):
        return self.service.get(user_id)
```

### WebSocket Support

```python
from pico_fastapi import controller, websocket
from fastapi import WebSocket

@controller(scope="websocket")
class ChatController:
    def __init__(self, manager: ChatManager):
        self.manager = manager

    @websocket("/ws/chat")
    async def chat(self, websocket: WebSocket):
        await self.manager.handle(websocket)
```

### Configurers (Middleware)

```python
from pico_fastapi import FastApiConfigurer
from pico_ioc import component
from fastapi import FastAPI

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Negative = outer middleware

    def configure(self, app: FastAPI) -> None:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
        )
```

---

## Why Pico-FastAPI?

| Concern | FastAPI Default | Pico-FastAPI |
|---------|-----------------|--------------|
| Dependency Injection | Function-based `Depends()` | Constructor-based |
| Architecture | Framework-driven | Domain-driven |
| Testing | Override `Depends()` | Override in container |
| Scopes | Manual | Automatic (request, session, websocket) |
| State Management | Global or request state | IoC container |

---

## Next Steps

1. **New to pico-fastapi?** Start with [Getting Started](./getting-started.md)
2. **Want examples?** Check the [How-To Guides](./how-to/index.md)
3. **Building production apps?** Read about [Configurers](./user-guide/configurers.md)
