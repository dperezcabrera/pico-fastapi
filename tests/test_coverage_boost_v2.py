"""Coverage boost tests for pico-fastapi.

Targets uncovered lines in factory.py:
- Line 67: Pydantic model_dump() in tuple response
- Line 72: Pydantic model_dump() in direct return
- Lines 99->101: Sync (non-async) controller method
- Line 133: WebSocket handler with extra path/query parameters
- Lines 136-137: WebSocket without type annotation (debug log)
"""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket
from starlette.responses import JSONResponse, Response

from pico_fastapi.factory import (
    _create_http_handler,
    _create_websocket_handler,
    _normalize_http_result,
    _priority_of,
)

# ── Pydantic model mock ──


class FakeModel:
    """Object with model_dump() to simulate Pydantic model."""

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self) -> dict:
        return self._data


# ── _normalize_http_result ──


class TestNormalizeHttpResult:
    def test_pydantic_model_in_tuple(self):
        """Line 67: tuple response with Pydantic model content."""
        model = FakeModel({"id": 1, "name": "Alice"})
        result = _normalize_http_result((model, 201))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 201

    def test_pydantic_model_direct(self):
        """Line 72: direct Pydantic model return."""
        model = FakeModel({"id": 2, "name": "Bob"})
        result = _normalize_http_result(model)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200


# ── Sync controller method (lines 99-101) ──


class TestSyncControllerMethod:
    @pytest.mark.asyncio
    async def test_sync_method_handler(self):
        """Lines 99-101: sync (non-async) controller method via _create_http_handler."""

        class SyncController:
            def get_data(self):
                return {"sync": True}

        container = AsyncMock()
        controller_instance = SyncController()
        container.aget = AsyncMock(return_value=controller_instance)

        sig = inspect.signature(SyncController.get_data)
        handler = _create_http_handler(container, SyncController, "get_data", sig)

        result = await handler()
        assert isinstance(result, Response)


# ── WebSocket with extra params (line 133) ──


class TestWebSocketExtraParams:
    @pytest.mark.asyncio
    async def test_websocket_with_extra_path_params(self):
        """Line 133: WebSocket handler with additional parameters beyond WebSocket."""

        class WsController:
            async def connect(self, ws: WebSocket, room_id: str):
                pass

        container = AsyncMock()
        controller_instance = WsController()
        container.aget = AsyncMock(return_value=controller_instance)

        sig = inspect.signature(WsController.connect)
        handler = _create_websocket_handler(container, WsController, "connect", sig)

        # Verify the handler's signature has websocket + room_id (not ws)
        handler_sig = inspect.signature(handler)
        param_names = list(handler_sig.parameters.keys())
        assert "websocket" in param_names
        assert "room_id" in param_names
        assert "ws" not in param_names  # ws replaced by websocket


class TestWebSocketNoAnnotation:
    def test_no_websocket_annotation_defaults(self):
        """Lines 136-137: WebSocket handler without WebSocket type annotation."""

        class WsController:
            async def connect(self, ws):
                pass

        container = MagicMock()
        sig = inspect.signature(WsController.connect)
        handler = _create_websocket_handler(container, WsController, "connect", sig)

        handler_sig = inspect.signature(handler)
        param_names = list(handler_sig.parameters.keys())
        assert "websocket" in param_names


# ── _priority_of exception handling ──


class TestPriorityOfException:
    def test_priority_non_int_returns_zero(self):
        """_priority_of with non-convertible priority falls back to 0."""

        class BadConfigurer:
            priority = "not-a-number"

        assert _priority_of(BadConfigurer()) == 0
