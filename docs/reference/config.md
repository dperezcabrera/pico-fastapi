# FastAPI configuration

This module defines two building blocks to configure a FastAPI application in a composable, dependency-injection-friendly way:

- FastApiSettings: a dataclass that carries basic application metadata (title, version, debug) and is designed to be provided by a pico_ioc container.
- FastApiConfigurer: a protocol (interface) for pluggable components that can mutate/configure a FastAPI app. Multiple configurers can be registered and executed in a deterministic order using a priority.

Use these together to bootstrap your app with clear separation between application settings and configuration steps such as adding middleware, routers, and event handlers.

## FastApiSettings

What it is:
- An immutable dataclass that holds basic FastAPI settings.
- Intended to be injected where needed using pico_ioc.

Fields:
- title: str — The application title (propagated to FastAPI).
- version: str — The application version (propagated to FastAPI).
- debug: bool — Whether to run FastAPI in debug mode.

How to use:
- Register a single FastApiSettings instance in your pico_ioc container.
- Use it when instantiating FastAPI, or inject into configurers for conditional behavior.

Example:
```python
from fastapi import FastAPI
from pico_ioc import Container
from yourpkg.config import FastApiSettings  # adjust import path

# 1) Compose DI container with settings
container = Container()
container.register_instance(FastApiSettings(
    title="Example API",
    version="1.0.0",
    debug=True,
))

# 2) Resolve settings and use them to build the app
settings = container.resolve(FastApiSettings)
app = FastAPI(
    title=settings.title,
    version=settings.version,
    debug=settings.debug,
)
```

## FastApiConfigurer protocol

What it is:
- A protocol defining a uniform way to configure a FastAPI app.
- Lets you register multiple independent configurers and run them in a defined order.

Members:
- priority(self) -> int: Returns a numeric priority used to sort configurers. Use this to control execution order.
- configure(self, app) -> None: Receives the FastAPI app instance and performs configuration (e.g., include routers, add middleware, register events).

Typical use cases:
- Add middleware (CORS, logging, tracing).
- Register routers and dependencies.
- Mount sub-apps and static files.
- Register startup/shutdown event handlers.

Example: implement and register configurers
```python
from fastapi import FastAPI
from pico_ioc import Container
from yourpkg.config import FastApiConfigurer, FastApiSettings  # adjust import path

# A configurer that sets up an API router
class ApiRouterConfigurer(FastApiConfigurer):
    def priority(self) -> int:
        # Run after low-level middleware, before docs tweaks
        return 200

    def configure(self, app: FastAPI) -> None:
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/health")
        def health():
            return {"status": "ok"}

        app.include_router(router, prefix="/api")

# A configurer that adds a simple middleware
class LoggingMiddlewareConfigurer(FastApiConfigurer):
    def priority(self) -> int:
        # Run early to capture as much as possible
        return 100

    def configure(self, app: FastAPI) -> None:
        @app.middleware("http")
        async def log_requests(request, call_next):
            response = await call_next(request)
            # Add your logging here
            return response

# A configurer that depends on settings (DI via pico_ioc)
class DebugOnlyDocsConfigurer(FastApiConfigurer):
    def __init__(self, settings: FastApiSettings) -> None:
        self._settings = settings

    def priority(self) -> int:
        return 300

    def configure(self, app: FastAPI) -> None:
        # Example of conditional behavior based on settings
        if not self._settings.debug:
            # Disable Swagger UI in non-debug environments
            app.docs_url = None
            app.redoc_url = None
```

Register and apply configurers with the container:
```python
from fastapi import FastAPI
from pico_ioc import Container
from yourpkg.config import FastApiSettings, FastApiConfigurer  # adjust import path

container = Container()

# Settings instance
container.register_instance(FastApiSettings(
    title="Example API",
    version="1.0.0",
    debug=True,
))

# Register configurers; exact API depends on pico_ioc, adjust as needed
container.register(FastApiConfigurer, LoggingMiddlewareConfigurer)
container.register(FastApiConfigurer, ApiRouterConfigurer)
container.register(FastApiConfigurer, DebugOnlyDocsConfigurer)

# Build the app
settings = container.resolve(FastApiSettings)
app = FastAPI(
    title=settings.title,
    version=settings.version,
    debug=settings.debug,
)

# Resolve all configurers and apply them in priority order
# Replace `resolve_all` with the appropriate pico_ioc API if different
configurers = container.resolve_all(FastApiConfigurer)
configurers = sorted(configurers, key=lambda c: c.priority())

for cfg in configurers:
    cfg.configure(app)
```

Notes on priority:
- Priority is used solely to order configurers. Choose a consistent convention, e.g., smaller numbers run earlier.
- Consider grouping numbers by concern (100 for core/middleware, 200 for routers, 300 for documentation, etc.) to leave room for expansion.

Testing a configurer:
```python
from fastapi import FastAPI

def test_api_router_configurer_adds_routes():
    app = FastAPI()
    cfg = ApiRouterConfigurer()
    cfg.configure(app)

    routes = {r.path for r in app.routes}
    assert "/api/health" in routes
```

Summary:
- FastApiSettings provides injectable core settings for FastAPI instantiation.
- FastApiConfigurer defines a simple contract for modular, ordered app configuration.
- Register settings and configurers in pico_ioc, construct the app from settings, then resolve and execute all configurers in priority order.