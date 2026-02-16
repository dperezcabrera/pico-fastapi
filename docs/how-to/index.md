# How-To Guides

Practical step-by-step guides for common tasks with pico-fastapi.

## Available Guides

| Guide | Description |
|-------|-------------|
| [Session Shopping Cart](./session-cart.md) | Implement session-scoped state with a shopping cart |
| [Apply Settings](./settings-applied.md) | Configure FastAPI app from YAML/environment |
| [WebSocket Chat](./websocket-chat.md) | Build a real-time chat with WebSocket support |
| [CORS Middleware](./cors.md) | Add CORS middleware using FastApiConfigurer |
| [WebSocket Controllers](./websocket.md) | Create WebSocket controllers with proper scope |
| [Testing Controllers](./testing.md) | Test controllers with TestClient, mocks, and overrides |

## Quick Reference

### Adding Middleware

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI

@component
class MyMiddlewareConfigurer(FastApiConfigurer):
    priority = -10  # Negative = outer middleware

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(MyMiddleware)
```

### Creating a Controller

```python
from pico_fastapi import controller, get, post

@controller(prefix="/api/items", tags=["Items"])
class ItemController:
    def __init__(self, service: ItemService):
        self.service = service

    @get("/")
    async def list_items(self):
        return self.service.list_all()

    @post("/")
    async def create_item(self, data: ItemCreate):
        return self.service.create(data)
```

### WebSocket Endpoint

```python
from pico_fastapi import controller, websocket
from fastapi import WebSocket

@controller(scope="websocket")
class WsController:
    @websocket("/ws")
    async def ws_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
```

### Testing with Mocks

```python
from pico_boot import init
from fastapi import FastAPI
from fastapi.testclient import TestClient

def test_endpoint():
    container = init(
        modules=["myapp"],
        overrides={RealService: MockService()},
    )
    app = container.get(FastAPI)

    with TestClient(app) as client:
        response = client.get("/api/items")
        assert response.status_code == 200
```

### Loading Configuration

```python
from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from fastapi import FastAPI

config = configuration(YamlTreeSource("application.yaml"))

container = init(
    modules=["myapp"],
    config=config,
)

app = container.get(FastAPI)
```
