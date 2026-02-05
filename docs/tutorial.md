# 📘 Tutorial: Your First API in 5 Minutes

In this tutorial, we will build a simple “Greeting API” using `pico-fastapi`.
You will learn how to define services, create controllers, and wire everything together using the container.

> 💡 **Recommended:** Use `pico-boot` for auto-discovery and zero-config bootstrapping.
> If you are not using `pico-boot`, see the **Classic Version (without pico-boot)** linked below.

---

## ✅ Prerequisites

Install all required packages:

```bash
pip install fastapi uvicorn pico-ioc pico-fastapi pico-boot
```

---

# 🚀 Step 1: Define your Service

```python
# services.py
from pico_ioc import component

@component
class GreeterService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! Welcome to pico-fastapi."
```

---

# 🚀 Step 2: Create a Controller

```python
# controllers.py
from pico_fastapi import controller, get
from services import GreeterService

@controller(prefix="/greet")
class GreeterController:
    def __init__(self, service: GreeterService):
        self.service = service

    @get("/{name}")
    async def say_hello(self, name: str):
        return {"message": self.service.greet(name)}
```

---

# 🚀 Step 3: Wire the Application (Using pico-boot)

With `pico-boot`, `pico-fastapi` is automatically discovered via entry points.
You only need to list **your** modules.

```python
# main.py
from fastapi import FastAPI
from pico_boot import init

def create_app() -> FastAPI:
    container = init(
        modules=[
            "controllers",
            "services",
        ]
    )
    return container.get(FastAPI)

app = create_app()
```

✔ No `"pico_fastapi"`
✔ Auto-loaded
✔ Cleaner, safer bootstrapping

---

# 🚀 Step 4: Run It

```bash
uvicorn main:app --reload
```

Then open:
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

You will see the automatically generated Swagger UI with your `/greet/{name}` endpoint.

---

# 💡 Key Takeaways

1. **Clear separation of concerns**
   Your services contain pure business logic—not framework code.

2. **Constructor injection**
   Dependencies are explicit in `__init__`, fully managed by Pico-IoC.

3. **No global state**
   Scopes are created and cleaned up automatically via fastapi middleware.

4. **Auto-discovery with pico-boot**
   Your modules stay clean; pico-fastapi loads itself automatically.

---

# 📎 Classic Version (Without pico-boot)

If you want the version that uses **only `pico_ioc.init()`**,
you can find it here:

👉 **Classic Tutorial (init + manual module declaration)**
[https://github.com/dperezcabrera/pico-fastapi/blob/main/docs/tutorial-classic.md](https://github.com/dperezcabrera/pico-fastapi/blob/main/docs/tutorial-classic.md)
*(or wherever you want to place it; I can generate the file for you)*

The only change in the classic version is:

```python
container = init(
    modules=[
        "controllers",
        "services",
        "pico_fastapi",   # Required only without pico-boot
    ]
)
```


