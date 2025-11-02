# 📦 pico-fastapi

[![PyPI](https://img.shields.io/pypi/v/pico-fastapi.svg)](https://pypi.org/project/pico-fastapi/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-fastapi)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-ioc/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-fastapi/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-fastapi)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)

# Pico-FastAPI

**[Pico-FastAPI](https://github.com/dperezcabrera/pico-fastapi)** integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **[FastAPI](https://github.com/fastapi/fastapi)** — combining the power of *true inversion of control* with one of the most elegant and high-performance Python web frameworks.

It enables *constructor-based dependency injection*, scoped lifecycles, and clean architectural boundaries — all without global state or FastAPI’s function-based dependency injection.

> 🐍 Requires **Python 3.10+**  
> ⚡ Built on **FastAPI**, one of the fastest and most developer-friendly frameworks in Python  
> ✅ Fully async-compatible  
> ✅ Real IoC (constructor injection, not function injection)  
> ✅ Supports request, session, and websocket scopes

With **Pico-FastAPI**, you get the speed, elegance, and async performance of FastAPI — enhanced with a real IoC container for clean, testable, and maintainable applications.

---

## 🎯 Why pico-fastapi?

FastAPI’s built-in dependency system is function-based, which makes business logic tightly coupled to the framework.

`pico-fastapi` moves dependency resolution to the **IoC container**.

| Concern | FastAPI Default | pico-fastapi |
|--------|----------------|--------------|
| Dependency injection | Function-based | Constructor-based |
| Architecture | Framework-driven | Domain-driven |
| Testing | Must simulate DI functions | Component overrides at container init |
| Scopes | Manual or ad-hoc | `singleton`, `request`, `session`, `websocket` |

---

## 🧱 Core Features

- `@controller` class-based routing
- `@get`, `@post`, `@websocket`, etc.
- Constructor injection for controllers & services
- Automatic registration into FastAPI
- Scoped resolution via middleware (`request`, `session`, `websocket`)
- Full compatibility with Pico-IoC features: overrides, profiles, interceptors, cleanup

---

## 📦 Installation

```bash
pip install pico-fastapi
````

Also requires:

```bash
pip install pico-ioc fastapi
```

---

## 🚀 Quick Example

```python
# controllers.py
from pico_fastapi import controller, get

@controller(prefix="/api")
class ApiController:
    def __init__(self, service: "MyService"):
        self.service = service

    @get("/hello")
    async def hello(self):
        return {"msg": self.service.greet()}
```

```python
# services.py
class MyService:
    def greet(self) -> str:
        return "hello from service"
```

```python
# main.py
from pico_ioc import init
from fastapi import FastAPI

container = init(
    modules=[
        "controllers",
        "services",
        "pico_fastapi.factory",
    ]
)

app = container.get(FastAPI)  # ✅ retrieve the fully configured app
```

---

## 💬 WebSocket Example

```python
from pico_fastapi import controller, websocket
from fastapi import WebSocket

@controller
class ChatController:
    async def __init__(self):
        pass

    @websocket("/ws")
    async def chat(self, websocket: WebSocket):
        await websocket.accept()
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Echo: {message}")
```

---

## 🧪 Testing with Overrides

```python
from pico_ioc import init
from fastapi import FastAPI
from fastapi.testclient import TestClient

class FakeService:
    def greet(self) -> str:
        return "test"

container = init(
    modules=["controllers", "services", "pico_fastapi.factory"],
    overrides={ "MyService": FakeService() }
)

app = container.get(FastAPI)
client = TestClient(app)

assert client.get("/api/hello").json() == {"msg": "test"}
```

---

## ⚙️ How It Works

* `@controller` classes are registered automatically
* HTTP/WebSocket handlers are wrapped in a request or websocket scope
* All dependencies (services, config, state) are resolved through Pico-IoC
* Cleanup happens at application shutdown via lifespan integration

No global state. No implicit singletons. No magic.

---

## 📝 License

MIT — See `LICENSE`.


