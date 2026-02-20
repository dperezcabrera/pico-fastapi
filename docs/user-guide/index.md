# User Guide

This guide covers the core concepts and features of pico-fastapi in depth.

## Contents

| Section | Description |
|---------|-------------|
| [Configurers](./configurers.md) | Adding middleware and customizing the app |

---

## Quick Reference

### Controller Decorator

```python
@controller(
    prefix="/api",           # URL prefix
    tags=["API"],            # OpenAPI tags
    scope="request",         # Component scope (default: request)
    dependencies=[...],      # FastAPI dependencies
    responses={...},         # Default responses
)
class MyController:
    pass
```

### Route Decorators

```python
@get(path, **kwargs)        # HTTP GET
@post(path, **kwargs)       # HTTP POST
@put(path, **kwargs)        # HTTP PUT
@delete(path, **kwargs)     # HTTP DELETE
@patch(path, **kwargs)      # HTTP PATCH
@websocket(path, **kwargs)  # WebSocket
```

### Configurer Protocol

```python
class FastApiConfigurer(Protocol):
    @property
    def priority(self) -> int:
        return 0

    def configure_app(self, app: FastAPI) -> None:
        ...
```

### Settings

```python
@configured(target="self", prefix="fastapi", mapping="tree")
@dataclass
class FastApiSettings:
    title: str = "Pico-FastAPI App"
    version: str = "1.0.0"
    debug: bool = False
```

---

## Component Lifecycle

```
Application Start
      │
      ▼
┌─────────────────────────────────────┐
│           init(modules)              │
│  • Scan for @controller classes      │
│  • Register FastApiAppFactory        │
│  • Register FastApiSettings          │
│  • Register Configurers              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     container.get(FastAPI)           │
│  • Create FastAPI from settings      │
│  • Sort configurers by priority      │
│  • Apply inner configurers (≥0)      │
│  • Add PicoScopeMiddleware           │
│  • Apply outer configurers (<0)      │
│  • Register controller routes        │
└──────────────┬──────────────────────┘
               │
               ▼
      Application Ready
               │
   For each request/websocket:
               │
               ▼
┌─────────────────────────────────────┐
│         PicoScopeMiddleware          │
│  • Create request/websocket scope    │
│  • Resolve controller instance       │
│  • Handle request                    │
│  • Cleanup scope                     │
└─────────────────────────────────────┘
               │
               ▼
      Application Shutdown
               │
               ▼
┌─────────────────────────────────────┐
│       container.shutdown()           │
│  • Call @cleanup methods             │
│  • Release singleton resources       │
└─────────────────────────────────────┘
```

---

## Best Practices

### 1. Keep Controllers Thin

Controllers should delegate business logic to services:

```python
# Good
@controller(prefix="/users")
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    @get("/{id}")
    async def get_user(self, id: int):
        return self.service.get_user(id)

# Avoid: Business logic in controller
@controller(prefix="/users")
class UserController:
    def __init__(self, db: Database):
        self.db = db

    @get("/{id}")
    async def get_user(self, id: int):
        # Too much logic here
        user = self.db.query(User).filter_by(id=id).first()
        if not user:
            raise HTTPException(404)
        return self.serialize_user(user)
```

### 2. Use Appropriate Scopes

| Component Type | Recommended Scope |
|----------------|-------------------|
| Stateless services | `singleton` |
| Request-specific state | `request` |
| User session data | `session` |
| WS connection state | `websocket` |
| Database sessions | `request` |

### 3. Configure Middleware Priority Correctly

```python
# Outer middlewares (run before scope setup)
@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100  # Very outer

@component
class SessionConfigurer(FastApiConfigurer):
    priority = -50   # Outer, but after CORS

# Inner middlewares (run after scope setup)
@component
class AuthConfigurer(FastApiConfigurer):
    priority = 10    # Inner, can use scoped services
```

### 4. Use Overrides for Testing

```python
def test_with_mock():
    container = init(
        modules=["myapp"],
        overrides={
            Database: MockDatabase(),
            EmailService: MockEmailService(),
        },
    )
    # Tests run with mocks
```
