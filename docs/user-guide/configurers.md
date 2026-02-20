# Configurers

Configurers are the pico-fastapi way to add middleware and customize the FastAPI application. They provide a clean, composable pattern for application setup.

## What is a Configurer?

A Configurer is a class that implements the `FastApiConfigurer` protocol:

```python
from typing import Protocol
from fastapi import FastAPI

class FastApiConfigurer(Protocol):
    @property
    def priority(self) -> int:
        return 0

    def configure_app(self, app: FastAPI) -> None:
        ...
```

## Creating a Configurer

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI

@component
class MyConfigurer(FastApiConfigurer):
    priority = 0  # Default

    def configure_app(self, app: FastAPI) -> None:
        # Add middleware, routes, event handlers, etc.
        app.add_middleware(MyMiddleware)
```

## The Sandwich Pattern

Pico-fastapi uses a "sandwich" pattern for middleware ordering:

```
                    Request
                       │
                       ▼
┌──────────────────────────────────────────┐
│        Outer Middlewares (< 0)           │
│    (CORS, Session, Request Logging)      │
└──────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│         PicoScopeMiddleware              │
│  (Creates request/session/ws scopes)     │
└──────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│        Inner Middlewares (≥ 0)           │
│    (Auth, Rate Limiting, etc.)           │
└──────────────────────────────────────────┘
                       │
                       ▼
                   Handler
```

### Priority Values

| Priority | Position | When to Use |
|----------|----------|-------------|
| < 0 | Outer | Before scopes exist (CORS, sessions) |
| 0 | Inner | Default, after scopes exist |
| > 0 | Inner | After other inner middleware |

### Why This Matters

**Outer middleware** runs before `PicoScopeMiddleware`, meaning:
- Request and session scopes don't exist yet
- You cannot use request-scoped services

**Inner middleware** runs after `PicoScopeMiddleware`, meaning:
- Request and session scopes are available
- You can inject and use request-scoped services

## Common Configurer Patterns

### CORS Middleware

CORS must be outer to handle preflight requests:

```python
from fastapi.middleware.cors import CORSMiddleware
from pico_ioc import component
from pico_fastapi import FastApiConfigurer

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Very outer

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
```

### Session Middleware

Sessions must be outer so session data is available when creating session scope:

```python
from starlette.middleware.sessions import SessionMiddleware
from pico_ioc import component, configured
from pico_fastapi import FastApiConfigurer
from dataclasses import dataclass

@configured(target="self", prefix="session", mapping="tree")
@dataclass
class SessionSettings:
    secret_key: str = "change-me-in-production"
    max_age: int = 3600

@component
class SessionConfigurer(FastApiConfigurer):
    priority = -50  # Outer, after CORS

    def __init__(self, settings: SessionSettings):
        self.settings = settings

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(
            SessionMiddleware,
            secret_key=self.settings.secret_key,
            max_age=self.settings.max_age,
        )
```

### Authentication Middleware

Auth can be inner if it needs request-scoped services:

```python
from pico_ioc import component, PicoContainer
from pico_fastapi import FastApiConfigurer

class AuthMiddleware:
    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # Get request-scoped auth service
                auth_service = await self.container.aget(AuthService)
                user = await auth_service.validate_token(token)
                if user:
                    # Store user in request-scoped context
                    user_ctx = await self.container.aget(UserContext)
                    user_ctx.set_user(user)

        await self.app(scope, receive, send)

@component
class AuthConfigurer(FastApiConfigurer):
    priority = 10  # Inner - needs request scope

    def __init__(self, container: PicoContainer):
        self.container = container

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(AuthMiddleware, container=self.container)
```

### Static Files

```python
from fastapi.staticfiles import StaticFiles
from pico_ioc import component, configured
from pico_fastapi import FastApiConfigurer
from dataclasses import dataclass

@configured(target="self", prefix="static", mapping="tree")
@dataclass
class StaticSettings:
    directory: str = "static"
    path: str = "/static"

@component
class StaticFilesConfigurer(FastApiConfigurer):
    priority = -100  # Outer

    def __init__(self, settings: StaticSettings):
        self.settings = settings

    def configure_app(self, app: FastAPI) -> None:
        app.mount(
            self.settings.path,
            StaticFiles(directory=self.settings.directory),
            name="static",
        )
```

### Error Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pico_ioc import component
from pico_fastapi import FastApiConfigurer

@component
class ErrorHandlerConfigurer(FastApiConfigurer):
    priority = 0

    def configure_app(self, app: FastAPI) -> None:
        @app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc)},
            )

        @app.exception_handler(PermissionError)
        async def permission_error_handler(request: Request, exc: PermissionError):
            return JSONResponse(
                status_code=403,
                content={"detail": "Permission denied"},
            )
```

### Event Handlers

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer

@component
class EventConfigurer(FastApiConfigurer):
    priority = 0

    def configure_app(self, app: FastAPI) -> None:
        @app.on_event("startup")
        async def on_startup():
            print("Application starting...")

        @app.on_event("shutdown")
        async def on_shutdown():
            print("Application shutting down...")
```

## Configurer Dependencies

Configurers can have dependencies injected:

```python
from pico_ioc import component, PicoContainer
from pico_fastapi import FastApiConfigurer

@component
class MetricsConfigurer(FastApiConfigurer):
    priority = 0

    def __init__(
        self,
        container: PicoContainer,
        settings: MetricsSettings,
        metrics_service: MetricsService,
    ):
        self.container = container
        self.settings = settings
        self.metrics_service = metrics_service

    def configure_app(self, app: FastAPI) -> None:
        # Use injected dependencies
        if self.settings.enabled:
            app.add_middleware(
                MetricsMiddleware,
                service=self.metrics_service,
            )
```

## Order of Execution

When multiple configurers exist, they're processed in priority order:

```python
# Execution order during setup:
# 1. Inner configurers (priority >= 0), lowest first
# 2. PicoScopeMiddleware is added
# 3. Outer configurers (priority < 0), lowest first (most negative first)

@component
class A(FastApiConfigurer):
    priority = 10  # 2nd inner

@component
class B(FastApiConfigurer):
    priority = 5   # 1st inner

@component
class C(FastApiConfigurer):
    priority = -10  # 2nd outer

@component
class D(FastApiConfigurer):
    priority = -50  # 1st outer

# Setup order: B, A, [PicoScopeMiddleware], D, C
# Request flow: D -> C -> Scope -> A -> B -> Handler
```

## Best Practices

1. **Use meaningful priority values**: Don't use arbitrary numbers. Group related middleware:
   - -100 to -50: Infrastructure (CORS, sessions, static files)
   - -49 to -1: Pre-scope processing
   - 0: Default
   - 1 to 50: Auth, validation
   - 51+: Business logic middleware

2. **Document your priorities**: Add comments explaining why each priority was chosen.

3. **Keep configurers focused**: Each configurer should do one thing.

4. **Use configuration for settings**: Don't hardcode values.

5. **Test configurers**: Verify middleware is applied correctly.
