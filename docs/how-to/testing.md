# How to Test Controllers

This guide covers testing pico-fastapi controllers using `TestClient`, container overrides, and mock services.

---

## Basic Setup

A typical pico-fastapi test bootstraps a container, retrieves the `FastAPI` app, and uses Starlette's `TestClient`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pico_boot import init


def test_hello_endpoint():
    container = init(modules=["myapp"])
    app = container.get(FastAPI)

    with TestClient(app) as client:
        response = client.get("/api/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}
```

---

## Overriding Services with Mocks

Replace real services with test doubles using container overrides:

```python
from pico_ioc import component


# Production service
@component
class UserService:
    def get_user(self, user_id: int):
        return self.db.query(user_id)  # Hits the database


# Test double
class MockUserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "Test User"}


def test_get_user():
    container = init(
        modules=["myapp"],
        overrides={UserService: MockUserService()},
    )
    app = container.get(FastAPI)

    with TestClient(app) as client:
        response = client.get("/api/users/42")
        assert response.status_code == 200
        assert response.json()["name"] == "Test User"
```

---

## Shared Fixtures with pytest

Create reusable fixtures in `conftest.py`:

```python
# conftest.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pico_boot import init


@pytest.fixture
def container():
    return init(
        modules=["myapp"],
        overrides={
            UserService: MockUserService(),
            EmailService: MockEmailService(),
        },
    )


@pytest.fixture
def app(container):
    return container.get(FastAPI)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
```

Then use them in tests:

```python
def test_list_users(client):
    response = client.get("/api/users")
    assert response.status_code == 200


def test_create_user(client):
    response = client.post("/api/users", json={"name": "Alice"})
    assert response.status_code == 201
```

---

## Testing WebSocket Endpoints

```python
def test_websocket_echo(client):
    with client.websocket_connect("/ws/echo") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "Echo: ping"
```

---

## Testing Configurers in Isolation

You can test a `FastApiConfigurer` without bootstrapping the full container:

```python
from fastapi import FastAPI


def test_cors_configurer():
    app = FastAPI()
    configurer = CORSConfigurer()
    configurer.configure(app)

    # Verify middleware was added
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes
```

---

## Disabling Auto-Discovery in Tests

When using `pico-boot`, plugins are auto-discovered.  To disable this in tests:

```python
# conftest.py
import os


def pytest_configure(config):
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"
```

---

## Testing Tuple Responses

Controllers can return `(content, status_code)` or `(content, status_code, headers)` tuples:

```python
def test_not_found_returns_404(client):
    response = client.get("/api/items/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Not found"}
```

Where the controller method returns:

```python
@get("/items/{item_id}")
async def get_item(self, item_id: int):
    item = self.service.find(item_id)
    if item is None:
        return {"error": "Not found"}, 404
    return item
```

---

## Common Testing Pitfalls

| Problem | Cause | Fix |
|---|---|---|
| `NoControllersFoundError` | Controller module not in `modules=` list | Add the controller module to `init(modules=[...])` |
| Stale singleton between tests | Container reused across tests | Create a fresh container in each test or fixture |
| WebSocket test hangs | No `scope="websocket"` on controller | Add `@controller(scope="websocket")` |
| Mock not injected | Override key doesn't match the type hint | Ensure override key is the exact class used in `__init__` |

---

## Full Example

```python
# test_users.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pico_boot import init


class MockUserService:
    def __init__(self):
        self.users = {1: {"id": 1, "name": "Alice"}}

    def get_all(self):
        return list(self.users.values())

    def get(self, user_id: int):
        return self.users.get(user_id)

    def create(self, data):
        user = {"id": len(self.users) + 1, **data}
        self.users[user["id"]] = user
        return user


@pytest.fixture
def client():
    container = init(
        modules=["myapp"],
        overrides={UserService: MockUserService()},
    )
    app = container.get(FastAPI)
    with TestClient(app) as c:
        yield c


def test_list_users(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_user(client):
    response = client.post("/api/users", json={"name": "Bob"})
    assert response.status_code == 200
    assert response.json()["name"] == "Bob"


def test_get_user(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"
```
