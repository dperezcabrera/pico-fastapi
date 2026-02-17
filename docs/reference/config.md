# FastAPI configuration

This module defines two building blocks to configure a FastAPI application in a composable, dependency-injection-friendly way:

- FastApiSettings: a dataclass that carries basic application metadata (title, version, debug) and is designed to be provided by the pico-ioc container.
- FastApiConfigurer: a protocol (interface) for pluggable components that can mutate/configure a FastAPI app. Multiple configurers can be registered and executed in a deterministic order using a priority.

Use these together to bootstrap your app with clear separation between application settings and configuration steps such as adding middleware, routers, and event handlers.

## FastApiSettings

What it is:
- A `@configured` dataclass that holds basic FastAPI settings.
- Automatically loaded from configuration sources (YAML, env, dict) via the `fastapi` prefix.

Fields:
- title: str — The application title (propagated to FastAPI).
- version: str — The application version (propagated to FastAPI).
- debug: bool — Whether to run FastAPI in debug mode.

How to use:
- Provide a configuration source with a `fastapi` prefix when initializing the container.
- FastApiSettings is automatically populated and injected into the FastAPI app factory.

Example:
```yaml
# application.yaml
fastapi:
  title: Example API
  version: 1.0.0
  debug: true
```

```python
from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from fastapi import FastAPI

config = configuration(YamlTreeSource("application.yaml"))
container = init(modules=["myapp"], config=config)
app = container.get(FastAPI)

# app.title == "Example API"
# app.version == "1.0.0"
# app.debug == True
```

## FastApiConfigurer protocol

What it is:
- A protocol defining a uniform way to configure a FastAPI app.
- Lets you register multiple independent configurers and run them in a defined order.

Members:
- priority: int — A numeric priority used to sort configurers. Negative = outer middleware, non-negative = inner middleware.
- configure(self, app) -> None: Receives the FastAPI app instance and performs configuration (e.g., include routers, add middleware, register events).

Typical use cases:
- Add middleware (CORS, logging, tracing).
- Mount sub-apps and static files.
- Register error handlers and event handlers.

Example: implement and register configurers
```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI

@component
class LoggingConfigurer(FastApiConfigurer):
    priority = -10  # Outer middleware

    def configure(self, app: FastAPI) -> None:
        @app.middleware("http")
        async def log_requests(request, call_next):
            response = await call_next(request)
            return response

@component
class HealthRouteConfigurer(FastApiConfigurer):
    priority = 0

    def configure(self, app: FastAPI) -> None:
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/health")
        def health():
            return {"status": "ok"}

        app.include_router(router, prefix="/api")
```

Configurers are automatically discovered by the container. Just include the module in `init(modules=[...])`.

Notes on priority:
- Negative priority: outer middleware (runs before `PicoScopeMiddleware`).
- Non-negative priority: inner middleware (runs after `PicoScopeMiddleware`).
- Within the same group, lower numbers run first.

Testing a configurer:
```python
from fastapi import FastAPI

def test_health_route_configurer():
    app = FastAPI()
    cfg = HealthRouteConfigurer()
    cfg.configure(app)

    routes = {r.path for r in app.routes}
    assert "/api/health" in routes
```

Summary:
- FastApiSettings provides injectable core settings for FastAPI instantiation via `@configured`.
- FastApiConfigurer defines a simple contract for modular, ordered app configuration.
- Register configurers as `@component` classes; pico-ioc discovers and applies them automatically.

---

## Auto-generated API

::: pico_fastapi.config
