"""Unit tests for pico_fastapi decorators."""

import pytest

from pico_fastapi.decorators import (
    IS_CONTROLLER_ATTR,
    PICO_CONTROLLER_META,
    PICO_ROUTE_KEY,
    controller,
    delete,
    get,
    patch,
    post,
    put,
    websocket,
)


class TestControllerDecorator:
    """Tests for the @controller decorator."""

    def test_controller_sets_is_controller_attr(self):
        """Controller decorator marks class as a controller."""

        @controller
        class MyController:
            pass

        assert getattr(MyController, IS_CONTROLLER_ATTR) is True

    def test_controller_sets_empty_meta_by_default(self):
        """Controller decorator sets empty metadata by default."""

        @controller
        class MyController:
            pass

        meta = getattr(MyController, PICO_CONTROLLER_META, None)
        assert meta == {}

    def test_controller_with_prefix(self):
        """Controller decorator stores prefix in metadata."""

        @controller(prefix="/api/v1")
        class MyController:
            pass

        meta = getattr(MyController, PICO_CONTROLLER_META)
        assert meta["prefix"] == "/api/v1"

    def test_controller_with_tags(self):
        """Controller decorator stores tags in metadata."""

        @controller(tags=["users", "admin"])
        class MyController:
            pass

        meta = getattr(MyController, PICO_CONTROLLER_META)
        assert meta["tags"] == ["users", "admin"]

    def test_controller_with_multiple_kwargs(self):
        """Controller decorator stores all kwargs in metadata."""

        @controller(prefix="/api", tags=["test"], dependencies=["auth"])
        class MyController:
            pass

        meta = getattr(MyController, PICO_CONTROLLER_META)
        assert meta["prefix"] == "/api"
        assert meta["tags"] == ["test"]
        assert meta["dependencies"] == ["auth"]

    def test_controller_with_custom_scope(self):
        """Controller decorator passes scope to @component."""

        @controller(scope="websocket")
        class WsController:
            pass

        assert getattr(WsController, "_pico_infra", None) == "component"
        meta = getattr(WsController, "_pico_meta", {})
        assert meta.get("scope") == "websocket"

    def test_controller_default_scope_is_request(self):
        """Controller decorator uses 'request' scope by default."""

        @controller
        class MyController:
            pass

        meta = getattr(MyController, "_pico_meta", {})
        assert meta.get("scope") == "request"


class TestRouteDecorators:
    """Tests for HTTP route decorators."""

    def test_get_decorator_sets_route_info(self):
        """@get decorator sets route info with GET method."""

        @get("/users")
        def list_users():
            pass

        route_info = getattr(list_users, PICO_ROUTE_KEY)
        assert route_info["method"] == "GET"
        assert route_info["path"] == "/users"
        assert route_info["kwargs"] == {}

    def test_get_decorator_with_kwargs(self):
        """@get decorator passes kwargs to route info."""

        @get("/users", tags=["users"], summary="List users")
        def list_users():
            pass

        route_info = getattr(list_users, PICO_ROUTE_KEY)
        assert route_info["kwargs"]["tags"] == ["users"]
        assert route_info["kwargs"]["summary"] == "List users"

    def test_post_decorator_sets_route_info(self):
        """@post decorator sets route info with POST method."""

        @post("/users")
        def create_user():
            pass

        route_info = getattr(create_user, PICO_ROUTE_KEY)
        assert route_info["method"] == "POST"
        assert route_info["path"] == "/users"

    def test_put_decorator_sets_route_info(self):
        """@put decorator sets route info with PUT method."""

        @put("/users/{user_id}")
        def update_user(user_id: int):
            pass

        route_info = getattr(update_user, PICO_ROUTE_KEY)
        assert route_info["method"] == "PUT"
        assert route_info["path"] == "/users/{user_id}"

    def test_delete_decorator_sets_route_info(self):
        """@delete decorator sets route info with DELETE method."""

        @delete("/users/{user_id}")
        def delete_user(user_id: int):
            pass

        route_info = getattr(delete_user, PICO_ROUTE_KEY)
        assert route_info["method"] == "DELETE"
        assert route_info["path"] == "/users/{user_id}"

    def test_patch_decorator_sets_route_info(self):
        """@patch decorator sets route info with PATCH method."""

        @patch("/users/{user_id}")
        def patch_user(user_id: int):
            pass

        route_info = getattr(patch_user, PICO_ROUTE_KEY)
        assert route_info["method"] == "PATCH"
        assert route_info["path"] == "/users/{user_id}"

    def test_websocket_decorator_sets_route_info(self):
        """@websocket decorator sets route info with WEBSOCKET method."""

        @websocket("/ws")
        def websocket_handler():
            pass

        route_info = getattr(websocket_handler, PICO_ROUTE_KEY)
        assert route_info["method"] == "WEBSOCKET"
        assert route_info["path"] == "/ws"

    def test_decorator_preserves_function(self):
        """Route decorators preserve the original function."""

        @get("/test")
        def my_handler():
            return "hello"

        assert my_handler() == "hello"

    def test_decorator_preserves_async_function(self):
        """Route decorators preserve async functions."""

        @get("/test")
        async def my_async_handler():
            return "async hello"

        import asyncio

        result = asyncio.run(my_async_handler())
        assert result == "async hello"

    def test_multiple_decorators_last_wins(self):
        """When multiple route decorators applied, last one wins."""

        @post("/create")
        @get("/read")
        def handler():
            pass

        route_info = getattr(handler, PICO_ROUTE_KEY)
        # The outer decorator (post) is applied last and overwrites
        assert route_info["method"] == "POST"
        assert route_info["path"] == "/create"


class TestRouteDecoratorKwargs:
    """Tests for route decorator kwargs handling."""

    def test_response_model_kwarg(self):
        """Route decorators accept response_model."""
        from pydantic import BaseModel

        class UserResponse(BaseModel):
            id: int
            name: str

        @get("/user", response_model=UserResponse)
        def get_user():
            pass

        route_info = getattr(get_user, PICO_ROUTE_KEY)
        assert route_info["kwargs"]["response_model"] is UserResponse

    def test_status_code_kwarg(self):
        """Route decorators accept status_code."""

        @post("/users", status_code=201)
        def create_user():
            pass

        route_info = getattr(create_user, PICO_ROUTE_KEY)
        assert route_info["kwargs"]["status_code"] == 201

    def test_deprecated_kwarg(self):
        """Route decorators accept deprecated flag."""

        @get("/old-endpoint", deprecated=True)
        def old_endpoint():
            pass

        route_info = getattr(old_endpoint, PICO_ROUTE_KEY)
        assert route_info["kwargs"]["deprecated"] is True
