from typing import Any, Callable, Dict, Optional, Set, Type, TypeVar, ParamSpec, TypedDict, cast
from pico_ioc import component

P = ParamSpec("P")
R = TypeVar("R")

class RouteInfo(TypedDict):
    method: str
    path: str
    kwargs: Dict[str, Any]

PICO_ROUTE_KEY: str = "_pico_route_info"
PICO_CONTROLLER_META: str = "_pico_controller_meta"
CONTROLLERS: Set[Type[Any]] = set()

def controller(cls: Optional[Type[Any]] = None, *, scope: str = "request", **kwargs: Any) -> Callable[[Type[Any]], Type[Any]] | Type[Any]:
    def decorate(c: Type[Any]) -> Type[Any]:
        setattr(c, PICO_CONTROLLER_META, kwargs)
        CONTROLLERS.add(c)
        return component(c, scope=scope)
    return decorate if cls is None else decorate(cls)

def _create_route_decorator(method: str, path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        route_info: RouteInfo = {"method": method, "path": path, "kwargs": kwargs}
        setattr(func, PICO_ROUTE_KEY, cast(RouteInfo, route_info))
        return func
    return decorator

def get(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("GET", path, **kwargs)

def post(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("POST", path, **kwargs)

def put(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("PUT", path, **kwargs)

def delete(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("DELETE", path, **kwargs)

def patch(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("PATCH", path, **kwargs)

def websocket(path: str, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return _create_route_decorator("WEBSOCKET", path, **kwargs)

