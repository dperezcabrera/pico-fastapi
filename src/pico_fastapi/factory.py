import dataclasses
import inspect
from contextlib import asynccontextmanager
from typing import List, Any, Mapping
from fastapi import FastAPI, APIRouter, WebSocket
from starlette.responses import JSONResponse, Response
from pico_ioc import factory, provides, component, PicoContainer, configure
from .config import FastApiSettings, FastApiConfigurer
from .middleware import PicoScopeMiddleware
from .decorators import PICO_ROUTE_KEY, PICO_CONTROLLER_META, CONTROLLERS
from .exceptions import InvalidConfigurerError, NoControllersFoundError

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
        return JSONResponse(content=content, status_code=status, headers=headers)
    
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
    async def websocket_route_handler(websocket: WebSocket, **kwargs):
        controller_instance = await container.aget(controller_cls)
        method_to_call = getattr(controller_instance, method_name)
        await method_to_call(websocket, **kwargs)
    
    original_params = list(sig.parameters.values())[1:]
    new_params = [p for p in original_params if p.name != "websocket"]
    ws_param = inspect.Parameter("websocket", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=WebSocket)
    websocket_route_handler.__signature__ = sig.replace(parameters=[ws_param] + new_params)
    return websocket_route_handler

def register_controllers(app: FastAPI, container: PicoContainer):
    controller_classes = [cls for cls in CONTROLLERS if isinstance(cls, type)]
    if not controller_classes:
        raise NoControllersFoundError()
    for cls in controller_classes:
        meta = getattr(cls, PICO_CONTROLLER_META, {}) or {}
        router = APIRouter(
            prefix=meta.get("prefix", ""),
            tags=meta.get("tags", None),
            dependencies=meta.get("dependencies", None),
            responses=meta.get("responses", None),
        )
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            route_info = getattr(method, PICO_ROUTE_KEY, None)
            if not route_info:
                continue
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
        app.include_router(router)

@component
class PicoLifespanConfigurer:
    @configure
    def setup_fastapi(
        self,
        container: PicoContainer,
        app: FastAPI,
        configurers: List[FastApiConfigurer],
    ) -> None:
        valid_configurers = [c for c in configurers if isinstance(c, FastApiConfigurer) and callable(getattr(c, "configure", None))]
        if not all(isinstance(c, FastApiConfigurer) for c in valid_configurers):
            first_invalid = next((c for c in configurers if not isinstance(c, FastApiConfigurer)), None)
            if first_invalid is not None:
                raise InvalidConfigurerError(first_invalid)
        
        sorted_configurers = sorted(valid_configurers, key=_priority_of)
        for configurer in sorted_configurers:
            configurer.configure(app)
        
        register_controllers(app, container)
        app.add_middleware(PicoScopeMiddleware, container=container)
        
        @asynccontextmanager
        async def lifespan_manager(app_instance):
            yield
            await container.cleanup_all_async()
            container.shutdown()
        
        app.router.lifespan_context = lifespan_manager

@factory
class FastApiAppFactory:
    @provides(FastAPI, scope="singleton")
    def create_fastapi_app(
        self,
        settings: FastApiSettings,
    ) -> FastAPI:
        return FastAPI(**dataclasses.asdict(settings))
