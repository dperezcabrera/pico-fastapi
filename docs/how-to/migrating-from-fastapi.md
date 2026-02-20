# Migrating from Vanilla FastAPI

This guide maps FastAPI patterns to their pico-fastapi equivalents.
It covers route definitions, dependency injection, middleware, testing, and
the application entry point.

---

## At a glance

| Concept | Vanilla FastAPI | pico-fastapi |
|---|---|---|
| Routes | `@app.get("/path")` on functions | `@get("/path")` on class methods |
| Dependencies | `Depends()` in function parameters | Constructor injection via `__init__` |
| State | `app.state` or global variables | Scoped components (singleton, request, session) |
| Middleware | `app.add_middleware(...)` | `FastApiConfigurer` with priority |
| Testing | Override `Depends()` | Container overrides |
| App creation | `app = FastAPI()` | `app = container.get(FastAPI)` |

---

## 1. Routes: functions to controller methods

### Before

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": "Alice"}

@app.post("/api/users")
async def create_user(data: UserCreate):
    return {"id": 2, **data.model_dump()}
```

### After

```python
from pico_fastapi import controller, get, post

@controller(prefix="/api/users", tags=["Users"])
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    @get("/")
    async def list_users(self):
        return self.service.get_all()

    @get("/{user_id}")
    async def get_user(self, user_id: int):
        return self.service.get(user_id)

    @post("/")
    async def create_user(self, data: UserCreate):
        return self.service.create(data)
```

**What changed:**

- Functions become methods on a class decorated with `@controller`
- `@app.get(...)` becomes `@get(...)` (imported from `pico_fastapi`)
- Path parameters, query parameters, and request bodies work exactly the
  same — pico-fastapi forwards all FastAPI route kwargs
- The controller groups related routes under a shared `prefix`

**What stayed the same:**

- Path parameter syntax (`{user_id}`)
- Pydantic request body parsing (`data: UserCreate`)
- Query parameters in the method signature
- All `response_model`, `status_code`, `summary`, etc. kwargs

---

## 2. Dependencies: `Depends()` to constructor injection

### Before

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

def get_user_service(db: Database = Depends(get_db)):
    return UserService(db)

@app.get("/api/users")
async def list_users(service: UserService = Depends(get_user_service)):
    return service.get_all()
```

### After

```python
from pico_ioc import component
from pico_fastapi import controller, get

@component(scope="singleton")
class Database:
    # container manages lifecycle
    pass

@component
class UserService:
    def __init__(self, db: Database):     # injected by the container
        self.db = db

    def get_all(self):
        return self.db.query_all()

@controller(prefix="/api/users")
class UserController:
    def __init__(self, service: UserService):   # injected by the container
        self.service = service

    @get("/")
    async def list_users(self):
        return self.service.get_all()
```

**What changed:**

- No `Depends()` chains — dependencies are declared in `__init__`
- `@component` registers the class with the container
- Lifecycle (scope, cleanup) is managed by the container, not by
  generator functions with `yield`

**When to still use `Depends()`:**

`Depends()` is still useful for **request-specific values** that come from
the HTTP request itself and don't belong in the container:

```python
from fastapi import Depends, Header

def get_current_user(authorization: str = Header(...)):
    return decode_token(authorization)

@controller(prefix="/api/profile")
class ProfileController:
    def __init__(self, service: ProfileService):  # container injection
        self.service = service

    @get("/")
    async def get_profile(self, user=Depends(get_current_user)):  # request-level
        return self.service.get(user.id)
```

**Rule of thumb:**

- **Services, repos, config** -> constructor injection (`__init__`)
- **Current user, headers, cookies** -> `Depends()` in the route method

---

## 3. Middleware: `app.add_middleware()` to configurers

### Before

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)
```

### After

```python
from pico_ioc import component
from pico_fastapi import FastApiConfigurer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@component
class CORSConfigurer(FastApiConfigurer):
    priority = -100     # outer — runs before scope middleware

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_methods=["*"],
        )
```

**What changed:**

- Middleware is added inside a `FastApiConfigurer`, not at the module level
- The configurer has a `priority` that controls ordering relative to the
  scope middleware (see [Configurers guide](../user-guide/configurers.md))
- Configurers can inject dependencies (settings, services) via `__init__`

**Priority cheatsheet:**

| Middleware | Suggested priority | Why |
|---|---|---|
| CORS | `-100` | Must handle preflight before anything |
| Session | `-50` | Session cookie needed before scopes |
| Auth (token parsing) | `10` | Can use request-scoped services |
| Rate limiting | `20` | After auth (to know who the user is) |
| Logging | `-10` or `5` | Outer = raw; inner = with user context |

---

## 4. Error handlers

### Before

```python
@app.exception_handler(ValueError)
async def handle_value_error(request, exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})
```

### After — option A: in a configurer

```python
@component
class ErrorHandlerConfigurer(FastApiConfigurer):
    priority = 0

    def configure_app(self, app: FastAPI) -> None:
        @app.exception_handler(ValueError)
        async def handle_value_error(request, exc):
            return JSONResponse(status_code=400, content={"error": str(exc)})
```

### After — option B: directly on the app (in `main.py`)

If you only have one or two handlers, registering them on the app after
`container.get(FastAPI)` is also fine:

```python
app = container.get(FastAPI)

@app.exception_handler(ValueError)
async def handle_value_error(request, exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})
```

Both approaches work. Use configurers when the handler needs injected
dependencies.

---

## 5. Application entry point

### Before

```python
from fastapi import FastAPI

app = FastAPI(title="My API", version="1.0.0")

# Routes registered by decorating functions with @app.get, etc.
```

### After

```python
# application.yaml
# fastapi:
#   title: My API
#   version: 1.0.0

from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from fastapi import FastAPI

config = configuration(YamlTreeSource("application.yaml"))
container = init(modules=["myapp"], config=config)
app = container.get(FastAPI)
```

**What changed:**

- `FastAPI()` is created by the container's factory, not by you
- Settings come from config files / env vars, not constructor arguments
- Controllers, services, and configurers are wired automatically

---

## 6. Testing

### Before

```python
from fastapi.testclient import TestClient

def get_mock_db():
    return MockDatabase()

app.dependency_overrides[get_db] = get_mock_db

with TestClient(app) as client:
    response = client.get("/api/users")
```

### After

```python
from pico_boot import init
from fastapi import FastAPI
from fastapi.testclient import TestClient

container = init(
    modules=["myapp"],
    overrides={Database: MockDatabase()},
)
app = container.get(FastAPI)

with TestClient(app) as client:
    response = client.get("/api/users")
```

**What changed:**

- Override the **class**, not the factory function
- Overrides are passed to `init()`, not patched on the app
- Each `init()` creates a fresh container — no shared state between tests

---

## 7. APIRouter to controller

If you use `APIRouter` to group routes:

### Before

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/items", tags=["Items"])

@router.get("/")
async def list_items():
    ...

@router.post("/")
async def create_item(data: ItemCreate):
    ...

# In main.py
app.include_router(router)
```

### After

```python
from pico_fastapi import controller, get, post

@controller(prefix="/api/items", tags=["Items"])
class ItemController:
    def __init__(self, service: ItemService):
        self.service = service

    @get("/")
    async def list_items(self):
        ...

    @post("/")
    async def create_item(self, data: ItemCreate):
        ...

# No include_router needed — the container registers routes automatically
```

**What changed:**

- `APIRouter` becomes `@controller` — same kwargs (`prefix`, `tags`,
  `dependencies`, `responses`)
- No `app.include_router()` — pico-fastapi discovers and registers
  controllers automatically
- Routes get access to injected services via `self`

---

## Migration checklist

For each file in your existing FastAPI app:

- [ ] Replace `@app.get/post/put/delete/patch` with `@get/@post/@put/@delete/@patch`
      inside a `@controller` class
- [ ] Move `Depends()` chains for services to constructor injection
- [ ] Keep `Depends()` for request-specific data (current user, headers)
- [ ] Replace `app.add_middleware()` calls with `FastApiConfigurer` classes
- [ ] Replace `app = FastAPI()` with `app = container.get(FastAPI)`
- [ ] Replace `app.dependency_overrides` in tests with container `overrides`
- [ ] Add `@component` to every service, repository, and config class
- [ ] List all modules in `init(modules=[...])`

---

## See also

- [Getting Started](../getting-started.md) — full tutorial
- [Configurers guide](../user-guide/configurers.md) — middleware ordering
- [Testing guide](./testing.md) — testing patterns
- [FAQ](../faq.md) — common questions
