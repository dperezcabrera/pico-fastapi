"""Decorators for defining controllers and route methods.

Provides the ``@controller`` class decorator and HTTP/WebSocket method
decorators (``@get``, ``@post``, ``@put``, ``@delete``, ``@patch``,
``@websocket``) that attach routing metadata to controller methods.
"""

from typing import Any, Callable, Dict, Optional, ParamSpec, Type, TypedDict, TypeVar, cast

from pico_ioc import component

P = ParamSpec("P")
R = TypeVar("R")


class RouteInfo(TypedDict):
    """Metadata attached to a controller method by a route decorator.

    Attributes:
        method: HTTP method string (``"GET"``, ``"POST"``, etc.) or
            ``"WEBSOCKET"``.
        path: URL path for the route.
        kwargs: Extra keyword arguments forwarded to FastAPI's route
            registration (e.g. ``response_model``, ``status_code``).
    """

    method: str
    path: str
    kwargs: Dict[str, Any]


PICO_ROUTE_KEY: str = "_pico_route_info"
PICO_CONTROLLER_META: str = "_pico_controller_meta"
IS_CONTROLLER_ATTR: str = "_pico_is_controller"


def controller(
    cls: Optional[Type[Any]] = None, *, scope: str = "request", **kwargs: Any
) -> Callable[[Type[Any]], Type[Any]] | Type[Any]:
    """Mark a class as a pico-fastapi controller with DI and auto-routing.

    The decorated class is registered as a pico-ioc ``@component`` and its
    methods decorated with ``@get``, ``@post``, etc. are automatically
    registered as FastAPI routes at startup.

    Can be used with or without arguments::

        @controller
        class A: ...

        @controller(prefix="/api", tags=["Items"], scope="request")
        class B: ...

    Args:
        cls: The class being decorated (passed implicitly when used without
            parentheses).
        scope: pico-ioc scope for the controller instance.  Typical values
            are ``"request"`` (default) and ``"websocket"``.
        **kwargs: Additional metadata forwarded to the ``APIRouter``
            constructor.  Common keys: ``prefix``, ``tags``,
            ``dependencies``, ``responses``.

    Returns:
        The decorated class (registered as a pico-ioc component), or a
        decorator function if called with arguments.

    Example:
        .. code-block:: python

            @controller(prefix="/users", tags=["Users"])
            class UserController:
                def __init__(self, service: UserService):
                    self.service = service

                @get("/")
                async def list_users(self):
                    return self.service.list_all()
    """

    def decorate(c: Type[Any]) -> Type[Any]:
        setattr(c, PICO_CONTROLLER_META, kwargs)
        setattr(c, IS_CONTROLLER_ATTR, True)
        return component(c, scope=scope)

    return decorate if cls is None else decorate(cls)


def _create_route_decorator(method: str, path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Create a decorator that attaches route metadata to a function.

    Args:
        method: HTTP method string (e.g. ``"GET"``) or ``"WEBSOCKET"``.
        path: URL path for the route.
        **kwargs: Extra keyword arguments forwarded to FastAPI's route
            registration.

    Returns:
        A decorator that stores a :class:`RouteInfo` dict on the wrapped
        function under the ``_pico_route_info`` attribute.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        route_info: RouteInfo = {"method": method, "path": path, "kwargs": kwargs}
        setattr(func, PICO_ROUTE_KEY, cast(RouteInfo, route_info))
        return func

    return decorator


def get(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a GET endpoint on a controller method.

    Args:
        path: URL path for the route (e.g. ``"/"``, ``"/{id}"``).
        **kwargs: Additional FastAPI route parameters such as
            ``response_model``, ``status_code``, ``tags``, ``summary``.

    Returns:
        A decorator that attaches GET route metadata to the method.

    Example:
        .. code-block:: python

            @get("/items", response_model=list[Item])
            async def list_items(self):
                return self.service.get_all()
    """
    return _create_route_decorator("GET", path, **kwargs)


def post(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a POST endpoint on a controller method.

    Args:
        path: URL path for the route.
        **kwargs: Additional FastAPI route parameters such as
            ``response_model``, ``status_code``.

    Returns:
        A decorator that attaches POST route metadata to the method.

    Example:
        .. code-block:: python

            @post("/items", status_code=201)
            async def create_item(self, data: ItemCreate):
                return self.service.create(data)
    """
    return _create_route_decorator("POST", path, **kwargs)


def put(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a PUT endpoint on a controller method.

    Args:
        path: URL path for the route.
        **kwargs: Additional FastAPI route parameters.

    Returns:
        A decorator that attaches PUT route metadata to the method.

    Example:
        .. code-block:: python

            @put("/items/{id}")
            async def update_item(self, id: int, data: ItemUpdate):
                return self.service.update(id, data)
    """
    return _create_route_decorator("PUT", path, **kwargs)


def delete(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a DELETE endpoint on a controller method.

    Args:
        path: URL path for the route.
        **kwargs: Additional FastAPI route parameters.

    Returns:
        A decorator that attaches DELETE route metadata to the method.

    Example:
        .. code-block:: python

            @delete("/items/{id}", status_code=204)
            async def delete_item(self, id: int):
                pass
    """
    return _create_route_decorator("DELETE", path, **kwargs)


def patch(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a PATCH endpoint on a controller method.

    Args:
        path: URL path for the route.
        **kwargs: Additional FastAPI route parameters.

    Returns:
        A decorator that attaches PATCH route metadata to the method.

    Example:
        .. code-block:: python

            @patch("/items/{id}")
            async def patch_item(self, id: int, data: ItemPatch):
                return self.service.patch(id, data)
    """
    return _create_route_decorator("PATCH", path, **kwargs)


def websocket(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Define a WebSocket endpoint on a controller method.

    The WebSocket parameter is detected by type annotation
    (``ws: WebSocket``), not by argument name.

    Args:
        path: WebSocket route path (e.g. ``"/ws/chat"``).
        **kwargs: Additional FastAPI WebSocket route parameters.

    Returns:
        A decorator that attaches WebSocket route metadata to the method.

    Example:
        .. code-block:: python

            from fastapi import WebSocket

            @controller(scope="websocket")
            class ChatController:
                @websocket("/ws/chat")
                async def chat(self, ws: WebSocket):
                    await ws.accept()
                    data = await ws.receive_text()
                    await ws.send_text(f"Echo: {data}")
    """
    return _create_route_decorator("WEBSOCKET", path, **kwargs)
