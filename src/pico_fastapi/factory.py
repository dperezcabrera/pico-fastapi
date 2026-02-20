"""Application factory and startup wiring for pico-fastapi.

Contains :class:`FastApiAppFactory` (creates the ``FastAPI`` singleton),
:class:`PicoLifespanConfigurer` (applies configurers, registers controllers,
and attaches scope middleware), and the ``register_controllers()`` function.
"""

import dataclasses
import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, List

from fastapi import APIRouter, FastAPI, WebSocket
from pico_ioc import PicoContainer, component, configure, factory, provides
from starlette.responses import JSONResponse, Response

from .config import FastApiConfigurer, FastApiSettings
from .decorators import IS_CONTROLLER_ATTR, PICO_CONTROLLER_META, PICO_ROUTE_KEY
from .exceptions import NoControllersFoundError
from .middleware import PicoScopeMiddleware

logger = logging.getLogger(__name__)


def _priority_of(obj: Any) -> int:
    """Extract the integer priority from a configurer, defaulting to 0.

    Args:
        obj: An object expected to have a ``priority`` attribute.

    Returns:
        The integer priority, or ``0`` if the attribute is missing or
        cannot be converted.
    """
    try:
        return int(getattr(obj, "priority", 0))
    except Exception:
        return 0


def _normalize_http_result(result: Any) -> Response:
    """Convert a controller return value into a Starlette ``Response``.

    Supports the following return conventions:

    - A ``Response`` instance is returned as-is.
    - A ``(content, status_code)`` or ``(content, status_code, headers)``
      tuple is converted to a ``JSONResponse``.
    - Any other value (including Pydantic models) is serialized as JSON
      with status 200.

    Args:
        result: The value returned by a controller method.

    Returns:
        A Starlette ``Response`` suitable for the ASGI pipeline.
    """
    if isinstance(result, Response):
        return result

    if isinstance(result, tuple) and len(result) in (2, 3):
        content, status = result[0], result[1]
        headers = result[2] if len(result) == 3 else None
        # Convert Pydantic models to dict
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        return JSONResponse(content=content, status_code=status, headers=headers)

    # Convert Pydantic models to dict
    if hasattr(result, "model_dump"):
        result = result.model_dump()

    return JSONResponse(content=result)


def _create_http_handler(container: PicoContainer, controller_cls: type, method_name: str, sig: inspect.Signature):
    """Create an async HTTP route handler that resolves the controller via DI.

    The handler fetches a fresh controller instance from the container on
    every request, calls the named method, and normalizes the result into
    a ``Response``.

    Args:
        container: The pico-ioc container.
        controller_cls: The controller class to resolve.
        method_name: The name of the method to invoke.
        sig: The method's ``inspect.Signature`` (used to build the
            wrapper's signature, excluding ``self``).

    Returns:
        An async function suitable for ``APIRouter.add_api_route()``.
    """

    async def http_route_handler(**kwargs):
        controller_instance = await container.aget(controller_cls)
        method_to_call = getattr(controller_instance, method_name)
        res = method_to_call(**kwargs)
        if inspect.isawaitable(res):
            res = await res
        return _normalize_http_result(res)

    params = list(sig.parameters.values())[1:]
    http_route_handler.__signature__ = sig.replace(parameters=params)
    return http_route_handler


def _create_websocket_handler(container: PicoContainer, controller_cls: type, method_name: str, sig: inspect.Signature):
    """Create an async WebSocket route handler that resolves the controller via DI.

    The handler detects the WebSocket parameter by its type annotation
    (``WebSocket``), not by name, allowing any parameter name
    (e.g. ``ws``, ``socket``).

    Args:
        container: The pico-ioc container.
        controller_cls: The controller class to resolve.
        method_name: The name of the WebSocket method to invoke.
        sig: The method's ``inspect.Signature``.

    Returns:
        An async function suitable for
        ``APIRouter.add_api_websocket_route()``.
    """
    original_params = list(sig.parameters.values())[1:]
    ws_param_name = None
    new_params = []

    for param in original_params:
        if param.annotation is WebSocket:
            ws_param_name = param.name
        else:
            new_params.append(param)

    if not ws_param_name:
        ws_param_name = "websocket"
        logger.debug(
            "No WebSocket-annotated parameter found in %s.%s, defaulting to 'websocket'",
            controller_cls.__name__,
            method_name,
        )

    async def websocket_route_handler(websocket: WebSocket, **kwargs):
        controller_instance = await container.aget(controller_cls)
        method_to_call = getattr(controller_instance, method_name)
        kwargs[ws_param_name] = websocket
        await method_to_call(**kwargs)

    ws_wrapper_param = inspect.Parameter("websocket", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=WebSocket)
    websocket_route_handler.__signature__ = sig.replace(parameters=[ws_wrapper_param] + new_params)
    return websocket_route_handler


def _find_controller_classes(container: PicoContainer) -> list[type]:
    """Find all classes marked with ``@controller`` in the container.

    Inspects the container's internal locator metadata to discover
    registered controller components.

    Args:
        container: The pico-ioc container to search.

    Returns:
        A list of controller classes found in the container.
    """
    locator = getattr(container, "_locator", None)
    if not locator:
        return []
    return [
        key for key, _ in locator._metadata.items() if isinstance(key, type) and getattr(key, IS_CONTROLLER_ATTR, False)
    ]


def _register_route(router: APIRouter, container: PicoContainer, cls: type, name: str, method, route_info: dict):
    """Register a single route on the router.

    Args:
        router: The ``APIRouter`` to add the route to.
        container: The pico-ioc container for DI resolution.
        cls: The controller class owning the method.
        name: The method name.
        method: The unbound method object.
        route_info: A :class:`RouteInfo` dict with ``method``, ``path``,
            and ``kwargs``.
    """
    sig = inspect.signature(method)
    method_type = route_info["method"]

    if method_type == "WEBSOCKET":
        handler_func = _create_websocket_handler(container, cls, name, sig)
        router.add_api_websocket_route(
            path=route_info["path"],
            endpoint=handler_func,
            **route_info["kwargs"],
        )
    else:
        handler_func = _create_http_handler(container, cls, name, sig)
        router.add_api_route(
            path=route_info["path"],
            endpoint=handler_func,
            methods=[method_type],
            **route_info["kwargs"],
        )


def _create_router_for_controller(container: PicoContainer, cls: type) -> APIRouter:
    """Create and configure an ``APIRouter`` for a controller class.

    Reads controller metadata (prefix, tags, dependencies, responses)
    from the class and registers all decorated methods as routes.

    Args:
        container: The pico-ioc container.
        cls: The controller class.

    Returns:
        A configured ``APIRouter`` with all the controller's routes.
    """
    meta = getattr(cls, PICO_CONTROLLER_META, {}) or {}
    router = APIRouter(
        prefix=meta.get("prefix", ""),
        tags=meta.get("tags", None),
        dependencies=meta.get("dependencies", None),
        responses=meta.get("responses", None),
    )

    for name, method in inspect.getmembers(cls, inspect.isfunction):
        route_info = getattr(method, PICO_ROUTE_KEY, None)
        if route_info:
            _register_route(router, container, cls, name, method, route_info)

    return router


def register_controllers(app: FastAPI, container: PicoContainer):
    """Discover and register all ``@controller`` classes with the FastAPI app.

    Iterates over all controller classes found in the container's metadata,
    creates an ``APIRouter`` for each, and includes them in the app.

    Args:
        app: The FastAPI application instance.
        container: The pico-ioc container holding controller registrations.

    Raises:
        NoControllersFoundError: If no ``@controller``-decorated classes
            are found in the container.
    """
    controller_classes = _find_controller_classes(container)

    if not controller_classes:
        raise NoControllersFoundError()

    for cls in controller_classes:
        router = _create_router_for_controller(container, cls)
        app.include_router(router)


def _validate_configurers(configurers: List[Any]) -> List[FastApiConfigurer]:
    """Validate and filter configurers, discarding invalid ones with a warning.

    Each configurer is checked against the ``FastApiConfigurer`` protocol.
    Objects that do not satisfy the protocol are logged at WARNING level
    and excluded.

    Args:
        configurers: A list of candidate configurer objects.

    Returns:
        A filtered list containing only valid ``FastApiConfigurer``
        instances.
    """
    valid = []
    for c in configurers:
        if isinstance(c, FastApiConfigurer) and callable(getattr(c, "configure_app", None)):
            valid.append(c)
        else:
            logger.warning("Discarding invalid configurer %r: does not implement FastApiConfigurer protocol", c)
    return valid


def _split_configurers_by_priority(configurers: List[FastApiConfigurer]) -> tuple[list, list]:
    """Split configurers into inner (>= 0) and outer (< 0) groups by priority.

    Args:
        configurers: A list of validated configurers.

    Returns:
        A ``(inner, outer)`` tuple where *inner* configurers have
        ``priority >= 0`` and *outer* configurers have ``priority < 0``.
        Each group is sorted by ascending priority.
    """
    sorted_conf = sorted(configurers, key=_priority_of)
    inner = [c for c in sorted_conf if _priority_of(c) >= 0]
    outer = [c for c in sorted_conf if _priority_of(c) < 0]
    return inner, outer


def _apply_configurers(app: FastAPI, configurers: List[FastApiConfigurer]) -> None:
    """Apply a list of configurers to the app.

    Args:
        app: The FastAPI application instance.
        configurers: Configurers to apply, in order.
    """
    for configurer in configurers:
        configurer.configure_app(app)


def _create_lifespan_manager(container: PicoContainer):
    """Create the lifespan context manager for graceful shutdown.

    The returned context manager performs async cleanup of all container
    resources and then shuts down the container when the application
    stops.

    Args:
        container: The pico-ioc container to manage.

    Returns:
        An async context manager suitable for ``app.router.lifespan_context``.
    """

    @asynccontextmanager
    async def lifespan_manager(app_instance):
        yield
        await container.cleanup_all_async()
        container.shutdown()

    return lifespan_manager


@component
class PicoLifespanConfigurer:
    """Startup hook that wires FastAPI with pico-ioc at application boot.

    This component is auto-discovered by pico-ioc and runs during
    container configuration.  It performs the following steps in order:

    1. Validates and splits configurers by priority.
    2. Applies *inner* configurers (``priority >= 0``).
    3. Adds ``PicoScopeMiddleware``.
    4. Applies *outer* configurers (``priority < 0``).
    5. Registers all ``@controller`` routes.
    6. Attaches the lifespan manager for graceful shutdown.
    """

    @configure
    def setup_fastapi(
        self,
        container: PicoContainer,
        app: FastAPI,
        configurers: List[FastApiConfigurer],
    ) -> None:
        """Wire the FastAPI app with middleware, controllers, and lifespan.

        Args:
            container: The pico-ioc container.
            app: The FastAPI application instance.
            configurers: All discovered ``FastApiConfigurer`` implementations.
        """
        valid_configurers = _validate_configurers(configurers)
        inner, outer = _split_configurers_by_priority(valid_configurers)

        _apply_configurers(app, inner)
        app.add_middleware(PicoScopeMiddleware, container=container)
        _apply_configurers(app, outer)

        register_controllers(app, container)
        app.router.lifespan_context = _create_lifespan_manager(container)


@factory
class FastApiAppFactory:
    """Factory that creates the ``FastAPI`` application as a singleton.

    Reads :class:`FastApiSettings` (populated from configuration sources)
    and passes its fields as keyword arguments to the ``FastAPI()``
    constructor.  The resulting app is registered in the container with
    ``scope="singleton"``.

    Example:
        .. code-block:: python

            from fastapi import FastAPI
            from pico_boot import init

            container = init(modules=["myapp"])
            app = container.get(FastAPI)  # Created by FastApiAppFactory
    """

    @provides(FastAPI, scope="singleton")
    def create_fastapi_app(
        self,
        settings: FastApiSettings,
    ) -> FastAPI:
        """Create a FastAPI instance from the provided settings.

        Args:
            settings: Application settings (title, version, debug).

        Returns:
            A configured ``FastAPI`` application instance.
        """
        return FastAPI(**dataclasses.asdict(settings))
