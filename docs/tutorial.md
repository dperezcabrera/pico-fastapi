# Tutorial: Your First API in 5 Minutes

In this tutorial, we will build a simple "Greeting API" using `pico-fastapi`. You will learn how to define services, create controllers, and wire everything together using the container.

## Prerequisites

- Python 3.10+
- `fastapi`, `uvicorn`, and `pico-ioc` installed.

```bash
pip install fastapi uvicorn pico-ioc pico-fastapi
```

## Step 1: Define your Service

First, let's create a pure Python class that contains our business logic. Note that it knows nothing about HTTP or FastAPI.

```python
# services.py
from pico_ioc import component

@component
class GreeterService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! Welcome to pico-fastapi."
```

## Step 2: Create a Controller

Now, we create a controller to expose this logic via HTTP. Controllers are also components, but they use the `@controller` decorator.

```python
# controllers.py
from pico_fastapi import controller, get
from services import GreeterService

@controller(prefix="/greet")
class GreeterController:
    # Dependency Injection happens here in __init__
    def __init__(self, service: GreeterService):
        self.service = service

    @get("/{name}")
    async def say_hello(self, name: str):
        # Use the injected service
        message = self.service.greet(name)
        return {"message": message}
```

## Step 3: Wire the Application (Main)

Finally, we set up the container and create the FastAPI application.

```python
# main.py
from fastapi import FastAPI
from pico_ioc import PicoContainer, component
from pico_fastapi import PicoLifespanConfigurer, register_controllers

# Import your modules so the container can find the @component decorators
import services
import controllers

def create_app() -> FastAPI:
    app = FastAPI()
    
    # Initialize the container
    container = PicoContainer()
    
    # Create a generic configurer to handle lifecycle and middleware
    # Note: In a real app, you might use FastApiAppFactory, 
    # but here we do it manually for clarity.
    lifespan = PicoLifespanConfigurer()
    lifespan.setup_fastapi(container, app, configurers=[])
    
    return app

app = create_app()
```

## Step 4: Run it

Save the files and run the server using uvicorn:

```bash
uvicorn main:app --reload
```

Open your browser to `http://127.0.0.1:8000/docs`. You will see the Swagger UI with your `/greet/{name}` endpoint.

## Key Takeaways

1.  **Separation of Concerns**: `GreeterService` has no idea it's part of a web API.
2.  **Explicit Dependencies**: `GreeterController` explicitly asks for `GreeterService` in its constructor.
3.  **No Global State**: All resolution happens inside the container scope managed by `pico-fastapi`.

## Next Steps

Check out the [How-To Guides](how-to/index.md) to learn about WebSockets or applying generic Settings.

