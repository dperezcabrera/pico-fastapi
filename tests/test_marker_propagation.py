"""_pico_* markers must reach the registered endpoint (auth relies on it)."""

import sys

from fastapi import FastAPI
from pico_ioc import DictSource, component, configuration, init

from pico_fastapi import controller, get


@controller(prefix="/marked")
class MarkedController:
    @get("/anon")
    async def anon(self):
        return {"ok": True}


MarkedController.anon._pico_allow_anonymous = True
MarkedController.anon._pico_required_roles = ("operator",)


def _leaf_routes(routes):
    for r in routes:
        inner = getattr(r, "routes", None) or getattr(getattr(r, "original_router", None), "routes", None)
        if inner:
            yield from _leaf_routes(inner)
        else:
            yield r


def test_markers_reach_registered_endpoint(monkeypatch):
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")
    cfg = configuration(DictSource({"fastapi": {"title": "t"}}))
    container = init(modules=["pico_fastapi", sys.modules[__name__]], config=cfg)
    app = container.get(FastAPI)
    endpoints = {getattr(r, "path", ""): getattr(r, "endpoint", None) for r in _leaf_routes(app.routes)}
    ep = endpoints["/marked/anon"]
    assert getattr(ep, "_pico_allow_anonymous", False) is True
    assert getattr(ep, "_pico_required_roles", None) == ("operator",)
