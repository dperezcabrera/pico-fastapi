# src/pico_fastapi/factory.py
import dataclasses
import inspect
from contextlib import asynccontextmanager
from typing import List, Any, Tuple, Mapping
from fastapi import FastAPI, APIRouter, WebSocket
from starlette.responses import JSONResponse, Response
from pico_ioc import factory, provides, component, PicoContainer, configure
from .config import FastApiSettings, FastApiConfigurer
from .middleware import PicoScopeMiddleware
from .decorators import PICO_ROUTE_KEY, PICO_CONTROLLER_META, CONTROLLERS

def _is_configurer(obj: Any) -> bool:
    fn: Any = getattr(obj, "configure", None)
    return callable(fn)

def _priority_of(obj: Any) -> int:
    try:
        return int(getattr(obj, "priority", 0))
    except Exception:
        return 0

def _normalize_http_result(result: Any) -> Any:
    if isinstance(result, tuple) and len(result) in (2, 3):
        content = result[0]
        status = result[1]
        headers: Mapping[str, str] | None = None
        if len(result) == 3 and isinstance(result[2], Mapping):
            headers = result[2]  # type: ignore[assignment]
        return JSONResponse(content=content, status_code=int(status), headers=dict(headers or {}))
    return result

def _create_http_handler(container: PicoContainer, controller_cls: type, method_name: str, sig: inspect.Signature):
    async def http_route_handler(**kwargs):
        controller_instance = await container.aget(controller_cls)
        method_to_call = getattr(controller_instance, method_name)
        result = await method_to_call(**kwargs)
        return _normalize_http_result(result)
    params = list(sig.parameters.values())[1:]
    http_route_handler.__signature__ = sig.replace(parameters=params)
    return http_route_handler

def _create_websocket_handler(_: PicoContainer, __: type, ___: str, sig: inspect.Signature):
    async def websocket_route_handler(websocket: WebSocket, **kwargs):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except Exception:
            pass
    original_params = list(sig.parameters.values())[1:]
    new_params = [p for p in original_params if p.name != "websocket"]
    ws_param = inspect.Parameter("websocket", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=WebSocket)
    websocket_route_handler.__signature__ = sig.replace(parameters=[ws_param] + new_params)
    return websocket_route_handler

def register_controllers(app: FastAPI, container: PicoContainer):
    controller_classes = [cls for cls in CONTROLLERS if isinstance(cls, type)]
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
        valid_configurers = [c for c in configurers if _is_configurer(c)]
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

