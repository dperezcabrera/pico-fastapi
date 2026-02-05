# Getting Started

This guide walks you through creating your first FastAPI application with pico-fastapi in 5 minutes.

## Prerequisites

- **Python 3.11** or newer
- Basic understanding of FastAPI
- Basic understanding of dependency injection

## Installation

```bash
pip install pico-fastapi pico-boot uvicorn
```

This installs:

- `pico-fastapi` - FastAPI integration
- `pico-boot` - Auto-discovery bootstrapper
- `pico-ioc` - Core DI container (installed as dependency)
- `uvicorn` - ASGI server

---

## Understanding the Basics

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Controller** | A class decorated with `@controller` that groups related HTTP endpoints |
| **Route Decorators** | `@get`, `@post`, `@put`, `@delete`, `@patch`, `@websocket` |
| **Configurer** | A class that configures the FastAPI app (middleware, etc.) |
| **Scope** | Request lifecycle (request, session, websocket) |

### Import Pattern

```python
# Decorators from pico-ioc
from pico_ioc import component

# FastAPI decorators from pico-fastapi
from pico_fastapi import controller, get, post

# Container initialization from pico-boot
from pico_boot import init
```

---

## Your First Application

### Step 1: Create a Service

```python
# myapp/services.py
from pico_ioc import component

@component
class GreeterService:
    """A simple greeting service."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}! Welcome to pico-fastapi."

    def farewell(self, name: str) -> str:
        return f"Goodbye, {name}!"
```

### Step 2: Create a Controller

```python
# myapp/controllers.py
from pico_fastapi import controller, get
from myapp.services import GreeterService

@controller(prefix="/api/greet", tags=["Greetings"])
class GreetingController:
    """Controller for greeting endpoints."""

    def __init__(self, service: GreeterService):
        # Service is automatically injected
        self.service = service

    @get("/{name}")
    async def say_hello(self, name: str):
        """Greet a user by name."""
        message = self.service.greet(name)
        return {"message": message}

    @get("/{name}/goodbye")
    async def say_goodbye(self, name: str):
        """Say goodbye to a user."""
        message = self.service.farewell(name)
        return {"message": message}
```

### Step 3: Initialize the Application

```python
# myapp/main.py
from pico_boot import init
from fastapi import FastAPI

def create_app() -> FastAPI:
    # Initialize container - pico-fastapi is auto-discovered
    container = init(modules=[
        "myapp.services",
        "myapp.controllers",
    ])

    # Get the configured FastAPI app
    return container.get(FastAPI)

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Run the Application

```bash
uvicorn myapp.main:app --reload
```

Open your browser to:

- **API Docs**: http://127.0.0.1:8000/docs
- **Test Endpoint**: http://127.0.0.1:8000/api/greet/World

---

## Adding Configuration

### Step 1: Create Configuration File

```yaml
# application.yaml
fastapi:
  title: My Greeting API
  version: 1.0.0
  debug: true

greeting:
  default_language: en
```

### Step 2: Define Configuration Class

```python
# myapp/config.py
from dataclasses import dataclass
from pico_ioc import configured

@configured(target="self", prefix="greeting", mapping="tree")
@dataclass
class GreetingConfig:
    default_language: str = "en"
```

### Step 3: Use Configuration in Service

```python
# myapp/services.py
from pico_ioc import component
from myapp.config import GreetingConfig

GREETINGS = {
    "en": "Hello",
    "es": "Hola",
    "fr": "Bonjour",
}

@component
class GreeterService:
    def __init__(self, config: GreetingConfig):
        self.language = config.default_language

    def greet(self, name: str) -> str:
        greeting = GREETINGS.get(self.language, "Hello")
        return f"{greeting}, {name}!"
```

### Step 4: Load Configuration

```python
# myapp/main.py
from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from fastapi import FastAPI

def create_app() -> FastAPI:
    config = configuration(YamlTreeSource("application.yaml"))

    container = init(
        modules=[
            "myapp.config",
            "myapp.services",
            "myapp.controllers",
        ],
        config=config,
    )

    return container.get(FastAPI)

app = create_app()
```

---

## Adding Middleware with Configurers

Configurers let you add middleware and customize the FastAPI app.

### Understanding Priority

- **Positive priority (>= 0)**: Inner middleware, runs AFTER scope setup
- **Negative priority (< 0)**: Outer middleware, runs BEFORE scope setup

```
Request -> [Outer Middleware] -> [PicoScopeMiddleware] -> [Inner Middleware] -> Handler
```

### Example: CORS Middleware

```python
# myapp/configurers.py
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Outer middleware

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
```

### Example: Authentication Middleware

```python
# myapp/auth.py
from pico_ioc import component, PicoContainer
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI

class AuthMiddleware:
    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Access request-scoped auth service
            auth_service = await self.container.aget(AuthService)
            # ... validate token
        await self.app(scope, receive, send)

@component
class AuthConfigurer(FastApiConfigurer):
    priority = 10  # Inner middleware (after scope setup)

    def __init__(self, container: PicoContainer):
        self.container = container

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(AuthMiddleware, container=self.container)
```

---

## HTTP Methods

All standard HTTP methods are supported:

```python
from pico_fastapi import controller, get, post, put, delete, patch

@controller(prefix="/items")
class ItemController:
    @get("/")
    async def list_items(self):
        """GET /items"""
        return []

    @post("/")
    async def create_item(self, data: ItemCreate):
        """POST /items"""
        return {"id": 1, **data.dict()}

    @get("/{item_id}")
    async def get_item(self, item_id: int):
        """GET /items/{item_id}"""
        return {"id": item_id}

    @put("/{item_id}")
    async def update_item(self, item_id: int, data: ItemUpdate):
        """PUT /items/{item_id}"""
        return {"id": item_id, **data.dict()}

    @patch("/{item_id}")
    async def patch_item(self, item_id: int, data: ItemPatch):
        """PATCH /items/{item_id}"""
        return {"id": item_id}

    @delete("/{item_id}")
    async def delete_item(self, item_id: int):
        """DELETE /items/{item_id}"""
        return {"deleted": True}
```

---

## WebSocket Support

```python
from pico_fastapi import controller, websocket
from pico_ioc import component
from fastapi import WebSocket

@component(scope="websocket")
class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def broadcast(self, message: str):
        for conn in self.connections:
            await conn.send_text(message)

@controller(scope="websocket")
class ChatController:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    @websocket("/ws/chat")
    async def chat(self, websocket: WebSocket):
        await self.manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await self.manager.broadcast(f"Message: {data}")
        except:
            pass
```

---

## Testing

### Using Container Overrides

```python
# tests/test_greeting.py
import pytest
from fastapi.testclient import TestClient
from pico_boot import init
from fastapi import FastAPI

class MockGreeterService:
    def greet(self, name: str) -> str:
        return f"Mock greeting, {name}"

@pytest.fixture
def client():
    container = init(
        modules=["myapp.controllers"],
        overrides={GreeterService: MockGreeterService()},
    )
    app = container.get(FastAPI)

    with TestClient(app) as c:
        yield c

def test_greet_endpoint(client):
    response = client.get("/api/greet/World")
    assert response.status_code == 200
    assert "Mock greeting" in response.json()["message"]
```

### Disabling Auto-Discovery in Tests

```python
# tests/conftest.py
import os

def pytest_configure(config):
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"
```

---

## Project Structure

```
myapp/
├── application.yaml
├── main.py
├── config.py
├── services/
│   ├── __init__.py
│   └── greeting.py
├── controllers/
│   ├── __init__.py
│   └── greeting.py
├── configurers/
│   ├── __init__.py
│   ├── cors.py
│   └── auth.py
└── tests/
    ├── conftest.py
    └── test_greeting.py
```

---

## Next Steps

- [User Guide](./user-guide/index.md) - Deep dive into controllers and configurers
- [How-To Guides](./how-to/index.md) - Practical examples
- [FAQ](./faq.md) - Common questions
- [API Reference](./reference/index.md) - Complete API documentation
