# 🧭 Architecture Overview — pico-fastapi

`pico-fastapi` is a thin integration layer that connects **Pico-IoC**'s inversion-of-control container with **FastAPI**'s routing and request handling.  
Its purpose is not to replace FastAPI — but to ensure that **application logic is resolved through the container**, not through function-based dependency injection.

---

## 1. High-Level Design

```

```
            ┌─────────────────────────────┐
            │          FastAPI            │
            │   (HTTP / WebSocket App)    │
            └──────────────┬──────────────┘
                           │
                      Route Registration
                           │
            ┌──────────────▼───────────────┐
            │       pico-fastapi           │
            │  (Controller → Route Glue)   │
            └──────────────┬───────────────┘
                           │
                    IoC Resolution
                           │
            ┌──────────────▼───────────────┐
            │           Pico-IoC           │
            │  (Container / Scopes / DI)   │
            └──────────────┬───────────────┘
                           │
                 Business Services, Repos,
                 Settings, Domain Logic
```

```

---

## 2. Data Flow (HTTP Request)

```

```
Request Arrives
       │
       ▼
```

┌───────────────────┐
│ PicoScopeMiddleware│  ← Creates a *request-scoped* container
└───────┬───────────┘
│
▼
┌───────────────────┐
│ FastAPI Router     │
└───────┬───────────┘
│ (handler is a wrapper)
▼
┌────────────────────────────────────────────────┐
│ controller_instance = container.aget(Controller)│
└────────────────────────────────────────────────┘
│
▼
Controller method executes
│
▼
Response out
│
▼
Request-scope disposed + async cleanup

````

### Key guarantees:
| Concern | Solution |
|--------|----------|
| No global singletons | Per-request scoped container |
| Constructor-based DI | All controllers resolved via IoC |
| Clean shutdown | Async cleanup via lifespan context |

---

## 3. Controller Model

- Controllers are **regular Python classes**
- They declare dependencies in `__init__`
- They use decorators to express routing

```python
@controller(prefix="/api")
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    @get("/users")
    async def list(self):
        return self.service.list_users()
````

No dependency injection *inside endpoint signatures*.

---

## 4. Route Registration Strategy

At startup:

1. `CONTROLLERS` collects all classes decorated with `@controller`.
2. For each method with `@get`, `@post`, etc., pico-fastapi registers a FastAPI route.
3. Each route uses a dynamically generated wrapper:

```python
async def route_handler(...):
    controller = await container.aget(ControllerClass)
    method = getattr(controller, method_name)
    return await method(...)
```

This ensures **all controller access goes through Pico-IoC**.

---

## 5. WebSocket Execution Model

WebSocket handlers:

* Receive a live `WebSocket` instance
* Are resolved via the request-scoped container just like HTTP routes
* pico-fastapi provides a simple echo loop by default in examples, but it does not enforce patterns

Lifecycle:

```
websocket.accept()
while active:
    message = websocket.receive_text()
    websocket.send_text(...)
```

Custom messaging layers (hubs, brokers, rooms) can be layered on top.

---

## 6. Scoping Model

| Scope                                 | Use Case                         | Behavior                           |
| ------------------------------------- | -------------------------------- | ---------------------------------- |
| `singleton`                           | shared infra (DB pools, clients) | One instance per app               |
| `request` *(default for controllers)* | HTTP/WebSocket request           | New instance / cleanup per request |
| `session` or custom                   | multi-step workflows             | Container-managed                  |

Scopes are enforced by **Pico-IoC**, not by FastAPI.

---

## 7. Cleanup & Lifespan

During FastAPI startup and shutdown, pico-fastapi:

* Attaches a `lifespan` context
* Ensures `await container.cleanup_all_async()` runs
* Then calls `container.shutdown()`

This guarantees all components supporting `async __aenter__/__aexit__` or `cleanup()` are safely closed.

---

## 8. Architectural Intent

**pico-fastapi exists to:**

* Decouple **business logic** from **web framework code**
* Support **hexagonal / clean architecture**
* Allow **test-friendly, replaceable dependencies**
* Enable **complex service graphs** with clear ownership

It does *not* attempt to:

* Replace FastAPI’s routing, docs, or validation system
* Provide magic auto-scanning of modules
* Hide the IoC container from developers

---

## 9. When to Use

Use pico-fastapi if your application values:

✔ Clear layering
✔ Replaceable services (e.g., real vs. mock, local vs. cloud)
✔ DDD, hexagonal architecture, microservices, or plugin systems
✔ Maintaining control over object creation and scopes

Avoid pico-fastapi if your app is:

✖ A small one-file script
✖ Built around function-based handlers
✖ Not concerned with composition or modularity

---

## 10. Summary

`pico-fastapi` is a **structural architecture tool**:
It lets FastAPI focus on *transport concerns*, while **Pico-IoC** owns *application composition*.

> Framework stays replaceable.
> Core stays pure.
> Dependencies stay explicit.


