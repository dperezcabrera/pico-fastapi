# 📦 pico-fastapi

[![PyPI](https://img.shields.io/pypi/v/pico-fastapi.svg)](https://pypi.org/project/pico-fastapi/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-fastapi)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-ioc/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-fastapi/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-fastapi)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-fastapi&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-fastapi)
[![Docs](https://img.shields.io/badge/Docs-pico--fastapi-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-fastapi/)

# Pico-FastAPI

**[Pico-FastAPI](https://github.com/dperezcabrera/pico-fastapi)** seamlessly integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **[FastAPI](https://github.com/fastapi/fastapi)**, bringing true inversion of control and constructor-based dependency injection to one of the fastest and most elegant Python web frameworks.

It provides scoped lifecycles, automatic controller registration, and clean architectural boundaries, without global state and without FastAPI’s function-based dependency system.

> 🐍 Requires Python 3.10+  
> ⚡ Built on FastAPI  
> ✅ Fully async-compatible  
> ✅ Real IoC with constructor injection  
> ✅ Supports singleton, request, session, and websocket scopes

With Pico-FastAPI you get the speed, clarity, and async performance of FastAPI, enhanced by a real IoC container for clean, testable, and maintainable applications.

---

## 🎯 Why pico-fastapi

FastAPI’s built-in dependency system is function-based, which often ties business logic to the framework. Pico-FastAPI moves dependency resolution into the IoC container, promoting separation of concerns and testability.

| Concern | FastAPI Default | pico-fastapi |
|----------|-----------------|---------------|
| Dependency injection | Function-based | Constructor-based |
| Architecture | Framework-driven | Domain-driven |
| Testing | Simulate DI calls | Override components in container |
| Scopes | Manual or ad-hoc | Automatic (singleton, request, session, websocket) |

---

## 🧱 Core Features

- Controller classes with `@controller`
- Route decorators: `@get`, `@post`, `@put`, `@delete`, `@patch`, `@websocket`
- Constructor injection for controllers and services
- Automatic registration into FastAPI
- Scoped resolution via middleware for request, session, and websocket
- Full Pico-IoC feature set: profiles, overrides, interceptors, cleanup hooks

---

## 📦 Installation

```bash
pip install pico-fastapi
````

Also install:

```bash
pip install pico-ioc fastapi
```

---

## 🚀 Quick Example

```python
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
from pico_ioc import component

@component
class MyService:
    def greet(self) -> str:
        return "hello from service"
```

```python
from pico_ioc import init
from fastapi import FastAPI

container = init(
    modules=[
        "controllers",
        "services",
        "pico_fastapi.factory",
    ]
)

app = container.get(FastAPI)
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
    overrides={"MyService": FakeService()}
)

app = container.get(FastAPI)
client = TestClient(app)

assert client.get("/api/hello").json() == {"msg": "test"}
```

---

## 📁 Static Files Configuration Example

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from pico_ioc import component, configured
from pico_fastapi import FastApiConfigurer

@configured(target="self", prefix="fastapi", mapping="tree")
@dataclass
class StaticSettings:
    static_dir: str = "public"
    static_url: str = "/static"

@component
class StaticFilesConfigurer(FastApiConfigurer):
    priority = -100
    def __init__(self, settings: StaticSettings):
        self.settings = settings
    def configure(self, app: FastAPI) -> None:
        app.mount(self.settings.static_url, StaticFiles(directory=self.settings.static_dir), name="static")
```

```python
from pico_ioc import init, configuration, YamlTreeSource
from fastapi import FastAPI

container = init(
    modules=[
        "pico_fastapi.factory",
        "static_config",
    ],
    config=configuration(
        YamlTreeSource("config.yml")
    ),
)

app = container.get(FastAPI)
```

```yaml
fastapi:
  title: "My App"
  version: "1.0.0"
  debug: true
  static_dir: "public"
  static_url: "/assets"
```

---

## 🔐 JWT Authentication Configuration Example

```python
import base64
import json
import hmac
import hashlib
from dataclasses import dataclass
from typing import Optional
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from pico_ioc import component, configured, PicoContainer
from pico_fastapi import FastApiConfigurer

def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _verify_hs256(token: str, secret: str) -> Optional[dict]:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    try:
        signature = _b64url_decode(sig_b64)
    except Exception:
        return None
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload_json = _b64url_decode(payload_b64)
        return json.loads(payload_json.decode())
    except Exception:
        return None

class JwtMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, container: PicoContainer, secret: str):
        super().__init__(app)
        self.container = container
        self.secret = secret
    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            claims = _verify_hs256(token, self.secret)
            if claims is not None:
                request.state.jwt_claims = claims
        response = await call_next(request)
        return response

@dataclass
class JwtSettings:
    secret: str = "changeme"
    header: str = "Authorization"

@component
class JwtConfigurer(FastApiConfigurer):
    priority = 10
    def __init__(self, container: PicoContainer, settings: JwtSettings):
        self.container = container
        self.settings = settings
    def configure(self, app: FastAPI) -> None:
        app.add_middleware(JwtMiddleware, container=self.container, secret=self.settings.secret)
```

```python
from pico_ioc import init
from fastapi import FastAPI, Request
from pico_fastapi import controller, get

@controller(prefix="/api")
class ProfileController:
    def __init__(self):
        pass
    @get("/me")
    async def me(self, request: Request):
        claims = getattr(request.state, "jwt_claims", None)
        if claims is None:
            return {"error": "not authenticated"}, 401
        return {"sub": claims.get("sub")}

container = init(
    modules=[
        "pico_fastapi.factory",
        "jwt_config",
        "controllers",
    ]
)

app = container.get(FastAPI)
```

---

## ⚙️ How It Works

* Controller classes are discovered and registered automatically
* Each route executes within its own request or websocket scope
* All dependencies are resolved via Pico-IoC
* Cleanup and teardown occur at FastAPI lifespan

No global state and no implicit singletons.

---

## 📝 License

MIT

