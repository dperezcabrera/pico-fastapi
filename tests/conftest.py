from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI, Request, WebSocket
from pico_ioc import PicoContainer, YamlTreeSource, cleanup, component, configuration, init
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from pico_fastapi import FastApiConfigurer, controller, get, post, websocket


@dataclass
class Claims:
    user_id: str
    roles: list[str] = field(default_factory=list)


@component(scope="request")
class UserContext:
    def __init__(self):
        self.claims: Claims | None = None
        self.is_authenticated: bool = False

    def load_from_claims(self, claims: Claims):
        self.claims = claims
        self.is_authenticated = True


@component(scope="request")
class AdminService:
    def __init__(self):
        self.id = id(self)

    def get_data(self):
        return f"Private data (request_id: {self.id})"


@component(scope="websocket")
class WebSocketManager:
    def __init__(self):
        self.id = id(self)

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text(f"Connected to WS Manager (id: {self.id})")
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo of {data} (id: {self.id})")
        except Exception:
            pass

    @cleanup
    def on_disconnect(self):
        print(f"WS Manager {self.id} cleaning up.")


@component(scope="session")
class ShoppingCart:
    def __init__(self):
        self.id = id(self)
        self.items = []

    def add_item(self, item: str):
        self.items.append(item)
        return self.items


def validate_and_extract_jwt(token: str) -> Claims:
    if token == "jwt_admin_token":
        return Claims(user_id="u-admin", roles=["admin"])
    if token == "jwt_user_token":
        return Claims(user_id="u-user", roles=["user"])
    raise PermissionError("Invalid JWT token")


class JwtSecurityMiddleware:
    def __init__(self, app, container: PicoContainer):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Standard ASGI header lookup
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("latin1")

            try:
                # Attempt to load user context
                user_ctx = await self.container.aget(UserContext)

                if auth_header and auth_header.startswith("Bearer "):
                    token_data = auth_header.split(" ")[1]
                    claims = validate_and_extract_jwt(token_data)
                    user_ctx.load_from_claims(claims)
            except Exception as e:
                # Debug print to see failures in tests
                print(f"DEBUG: Auth Middleware Failed: {e}")
                pass

        await self.app(scope, receive, send)


@component
class SecurityConfigurer(FastApiConfigurer):
    priority = 10

    def __init__(self, container: PicoContainer):
        self.container = container

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(JwtSecurityMiddleware, container=self.container)


@component
class OptionalSessionConfigurer(FastApiConfigurer):
    priority = -50

    def configure_app(self, app: FastAPI) -> None:
        app.add_middleware(SessionMiddleware, secret_key="my-session-secret-key")


@controller(prefix="/api")
class ApiController:
    def __init__(self, user_context: UserContext, admin_service: AdminService):
        self.user_context = user_context
        self.admin_service = admin_service

    @get("/admin/data", tags=["Admin"])
    async def get_admin_data(self):
        if not self.user_context.is_authenticated:
            return {"error": "Not authenticated"}, 401
        if "admin" not in self.user_context.claims.roles:
            return {"error": "Not authorized"}, 403
        return {"data": self.admin_service.get_data(), "user_id": self.user_context.claims.user_id}


@controller(prefix="/cart", tags=["HTTP Session"])
class CartController:
    def __init__(self, cart: ShoppingCart):
        self.cart = cart

    @post("/items/{item}")
    async def add_item(self, item: str):
        items = self.cart.add_item(item)
        return {"items": items, "cart_id": self.cart.id}

    @get("/items")
    async def get_cart(self):
        return {"items": self.cart.items, "cart_id": self.cart.id}


# CHANGED: Explicitly set scope="websocket" to avoid ScopeError (default is "request")
@controller(tags=["WebSocket"], scope="websocket")
class ChatController:
    def __init__(self, manager: WebSocketManager):
        self.manager = manager

    @websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket):
        await self.manager.handle_connection(websocket)


@pytest.fixture(scope="session")
def make_fastapi_app(tmp_path_factory):
    """Factory fixture for creating configured FastAPI apps."""

    def _create(yaml_content: str, extra_modules: list[str] | None = None):
        tmp = tmp_path_factory.mktemp("cfg")
        cfg = tmp / "config.yml"
        cfg.write_text(yaml_content, encoding="utf-8")
        modules = ["pico_fastapi.config", "pico_fastapi.factory"]
        if extra_modules:
            modules.extend(extra_modules)
        config = configuration(YamlTreeSource(str(cfg)))
        container = init(modules=modules, config=config)
        return container.get(FastAPI)

    return _create


@pytest.fixture(scope="session")
def app(make_fastapi_app):
    return make_fastapi_app(
        "fastapi:\n  title: 'Integration Test API'\n  version: '9.9.9'\n  debug: true\n",
        extra_modules=[__name__],
    )


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c
