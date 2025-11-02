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

**[Pico-FastAPI](https://github.com/dperezcabrera/pico-fastapi)** seamlessly integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **[FastAPI](https://github.com/fastapi/fastapi)** — bringing *true inversion of control* and *constructor-based dependency injection* to one of the fastest and most elegant Python frameworks.

It provides scoped lifecycles, automatic controller registration, and clean architectural boundaries — all without global state or FastAPI’s function-based dependency system.

> 🐍 Requires **Python 3.10+**  
> ⚡ Built on **FastAPI**, one of the fastest and most developer-friendly web frameworks in Python  
> ✅ Fully async-compatible  
> ✅ Real IoC (constructor injection, not function injection)  
> ✅ Supports `singleton`, `request`, `session`, and `websocket` scopes  

With **Pico-FastAPI**, you get the speed, clarity, and async performance of FastAPI — enhanced by a real IoC container for clean, testable, and maintainable applications.

---

## 🎯 Why pico-fastapi?

FastAPI’s built-in dependency system is *function-based*, which often ties business logic to the framework.  
`pico-fastapi` moves dependency resolution into the **IoC container**, promoting separation of concerns and testability.

| Concern | FastAPI Default | pico-fastapi |
|----------|-----------------|---------------|
| Dependency injection | Function-based | Constructor-based |
| Architecture | Framework-driven | Domain-driven |
| Testing | Simulate DI calls | Override components in container |
| Scopes | Manual/ad-hoc | Automatic (`singleton`, `request`, `session`, `websocket`) |

---

## 🧱 Core Features

- `@controller` class-based routing  
- Route decorators: `@get`, `@post`, `@put`, `@delete`, `@patch`, `@websocket`  
- Constructor injection for controllers and services  
- Automatic registration into FastAPI  
- Scoped resolution via middleware (`request`, `session`, `websocket`)  
- Full **Pico-IoC** feature set: profiles, overrides, interceptors, cleanup hooks  

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

app = container.get(FastAPI)  # ✅ fully configured FastAPI instance
```

---

## 💬 WebSocket Example

```python
from pico_fastapi import controller, websocket
from fastapi import WebSocket

@controller
class ChatController:
    @websocket("/ws")
    async def chat(self, websocket: WebSocket):
        await websocket.accept()
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Echo: {msg}")
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

* `@controller` classes are automatically discovered and registered
* Each route executes within its own request or websocket scope
* All dependencies (services, config, and state) are resolved via Pico-IoC
* Cleanup and teardown occur at FastAPI’s lifespan phase

No global state. No implicit singletons. No hidden magic — just pure IoC.

---

## 📝 License

MIT — see [`LICENSE`](LICENSE).
