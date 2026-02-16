# How to Add CORS Middleware

This guide shows how to add Cross-Origin Resource Sharing (CORS) middleware to a pico-fastapi application using the `FastApiConfigurer` protocol.

---

## Why CORS Needs Negative Priority

CORS middleware must handle preflight `OPTIONS` requests **before** the request reaches pico-ioc scopes or your controllers.  Use a negative `priority` so the configurer runs *outer* (before `PicoScopeMiddleware`).

```
Request Flow:
[CORS: priority -100] --> [PicoScopeMiddleware] --> [Controllers]
```

---

## Step 1: Create a CORS Configurer

```python
# configurers.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pico_ioc import component
from pico_fastapi import FastApiConfigurer


@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Outer middleware: before PicoScopeMiddleware

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://example.com"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
```

---

## Step 2: Include the Module

Make sure your configurer module is scanned during bootstrap:

```python
from pico_boot import init
from fastapi import FastAPI

container = init(modules=[
    "myapp.controllers",
    "myapp.services",
    "myapp.configurers",  # Include the configurer module
])
app = container.get(FastAPI)
```

With `pico-boot`, if `configurers.py` is inside a scanned package the configurer is discovered automatically.

---

## Loading Origins from Configuration

For production use, load allowed origins from your configuration file instead of hardcoding them:

```yaml
# application.yaml
cors:
  origins:
    - "https://example.com"
    - "https://admin.example.com"
```

```python
from dataclasses import dataclass, field
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pico_ioc import component, configured
from pico_fastapi import FastApiConfigurer


@configured(target="self", prefix="cors", mapping="tree")
@dataclass
class CORSSettings:
    origins: List[str] = field(default_factory=lambda: ["*"])


@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100

    def __init__(self, settings: CORSSettings):
        self.settings = settings

    def configure(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
```

---

## Testing CORS

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_cors_preflight(app: FastAPI):
    with TestClient(app) as client:
        response = client.options(
            "/api/endpoint",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
```

---

## Priority Cheat Sheet

| Middleware | Recommended Priority | Reason |
|---|---|---|
| CORS | -100 | Must handle preflight before anything else |
| Session | -50 | Session data needed before scope setup |
| Auth (token validation) | 10 | Can use request-scoped services |
| Rate Limiting | -10 | Reject early, before scope overhead |
