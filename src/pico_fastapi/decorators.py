# src/pico_fastapi/decorators.py
from typing import Set, Type
from pico_ioc import component

PICO_ROUTE_KEY = "_pico_route_info"
PICO_CONTROLLER_META = "_pico_controller_meta"
CONTROLLERS: Set[Type] = set()

def controller(cls=None, *, scope="request", **kwargs):
    def decorate(c):
        setattr(c, PICO_CONTROLLER_META, kwargs)
        CONTROLLERS.add(c)
        return component(c, scope=scope)
    return decorate if cls is None else decorate(cls)

def _create_route_decorator(method: str, path: str, **kwargs):
    def decorator(func):
        setattr(func, PICO_ROUTE_KEY, {"method": method, "path": path, "kwargs": kwargs})
        return func
    return decorator

def get(path: str, **kwargs): return _create_route_decorator("GET", path, **kwargs)
def post(path: str, **kwargs): return _create_route_decorator("POST", path, **kwargs)
def put(path: str, **kwargs): return _create_route_decorator("PUT", path, **kwargs)
def delete(path: str, **kwargs): return _create_route_decorator("DELETE", path, **kwargs)
def patch(path: str, **kwargs): return _create_route_decorator("PATCH", path, **kwargs)
def websocket(path: str, **kwargs): return _create_route_decorator("WEBSOCKET", path, **kwargs)

