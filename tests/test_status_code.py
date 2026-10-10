"""The status_code declared on a route decorator reaches the response."""

import sys

from fastapi import FastAPI
from pico_ioc import DictSource, configuration, init
from starlette.testclient import TestClient

from pico_fastapi import controller, delete, get, post


@controller(prefix="/items")
class ItemController:
    @post("", status_code=201)
    async def create(self):
        return {"id": 1}

    @delete("/{item_id}", status_code=204)
    async def remove(self, item_id: int):
        return None

    @post("/legacy", status_code=201)
    async def explicit(self):
        return {"error": "conflict"}, 409  # an explicit tuple still wins

    @get("")
    async def listing(self):
        return []


def _client():
    container = init(
        modules=["pico_fastapi", sys.modules[__name__]],
        config=configuration(DictSource({"fastapi": {"title": "t"}})),
    )
    return TestClient(container.get(FastAPI))


def test_declared_status_codes_reach_the_response():
    client = _client()
    created = client.post("/items")
    assert (created.status_code, created.json()) == (201, {"id": 1})
    removed = client.delete("/items/1")
    assert (removed.status_code, removed.content) == (204, b"")
    assert client.post("/items/legacy").status_code == 409
    assert client.get("/items").status_code == 200
