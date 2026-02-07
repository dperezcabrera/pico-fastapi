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
    try:
        return int(getattr(obj, "priority", 0))
    except Exception:
        return 0


def _normalize_http_result(result: Any) -> Response:
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
    """Find all classes marked with @controller in the container."""
    locator = getattr(container, "_locator", None)
    if not locator:
        return []
    return [
        key for key, _ in locator._metadata.items() if isinstance(key, type) and getattr(key, IS_CONTROLLER_ATTR, False)
    ]


def _register_route(router: APIRouter, container: PicoContainer, cls: type, name: str, method, route_info: dict):
    """Register a single route on the router."""
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
    """Create and configure a router for a controller class."""
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
    """Register all controllers with the FastAPI app."""
    controller_classes = _find_controller_classes(container)

    if not controller_classes:
        raise NoControllersFoundError()

    for cls in controller_classes:
        router = _create_router_for_controller(container, cls)
        app.include_router(router)


def _validate_configurers(configurers: List[Any]) -> List[FastApiConfigurer]:
    """Validate and filter configurers, discarding invalid ones with a warning."""
    valid = []
    for c in configurers:
        if isinstance(c, FastApiConfigurer) and callable(getattr(c, "configure", None)):
            valid.append(c)
        else:
            logger.warning("Discarding invalid configurer %r: does not implement FastApiConfigurer protocol", c)
    return valid


def _split_configurers_by_priority(configurers: List[FastApiConfigurer]) -> tuple[list, list]:
    """Split configurers into inner (>=0) and outer (<0) by priority."""
    sorted_conf = sorted(configurers, key=_priority_of)
    inner = [c for c in sorted_conf if _priority_of(c) >= 0]
    outer = [c for c in sorted_conf if _priority_of(c) < 0]
    return inner, outer


def _apply_configurers(app: FastAPI, configurers: List[FastApiConfigurer]) -> None:
    """Apply a list of configurers to the app."""
    for configurer in configurers:
        configurer.configure(app)


def _create_lifespan_manager(container: PicoContainer):
    """Create the lifespan context manager for cleanup."""

    @asynccontextmanager
    async def lifespan_manager(app_instance):
        yield
        await container.cleanup_all_async()
        container.shutdown()

    return lifespan_manager


@component
class PicoLifespanConfigurer:
    @configure
    def setup_fastapi(
        self,
        container: PicoContainer,
        app: FastAPI,
        configurers: List[FastApiConfigurer],
    ) -> None:
        valid_configurers = _validate_configurers(configurers)
        inner, outer = _split_configurers_by_priority(valid_configurers)

        _apply_configurers(app, inner)
        app.add_middleware(PicoScopeMiddleware, container=container)
        _apply_configurers(app, outer)

        register_controllers(app, container)
        app.router.lifespan_context = _create_lifespan_manager(container)


@factory
class FastApiAppFactory:
    @provides(FastAPI, scope="singleton")
    def create_fastapi_app(
        self,
        settings: FastApiSettings,
    ) -> FastAPI:
        return FastAPI(**dataclasses.asdict(settings))
