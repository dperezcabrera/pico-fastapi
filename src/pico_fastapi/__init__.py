"""pico-fastapi: FastAPI integration for pico-ioc.

Provides class-based controllers with constructor dependency injection,
automatic request/session/websocket scope management, and a pluggable
configurer system for middleware ordering.

Public API:
    Decorators: controller, get, post, put, delete, patch, websocket
    Protocols: FastApiConfigurer
    Dataclasses: FastApiSettings
    Factories: FastApiAppFactory
    Exceptions: PicoFastAPIError, NoControllersFoundError
"""

from .config import FastApiConfigurer, FastApiSettings
from .decorators import controller, delete, get, patch, post, put, websocket
from .exceptions import NoControllersFoundError, PicoFastAPIError
from .factory import FastApiAppFactory

__all__ = [
    "FastApiConfigurer",
    "FastApiSettings",
    "controller",
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "websocket",
    "FastApiAppFactory",
    "PicoFastAPIError",
    "NoControllersFoundError",
]
