"""FastAPI >= 0.142 ships built-in OpenTelemetry; pico-fastapi must not let it
add a second exporter to a provider the application already configured."""

import dataclasses
import inspect
import subprocess
import sys
import textwrap

import fastapi
import pytest
from packaging.version import Version

from pico_fastapi.config import FastApiSettings
from pico_fastapi.factory import FastApiAppFactory


def test_settings_default_disables_fastapi_exporter_autoconfiguration():
    assert FastApiSettings().telemetry == {"auto_configure": False}


def test_telemetry_setting_reaches_the_fastapi_constructor(monkeypatch):
    seen = {}
    target = inspect.unwrap(FastApiAppFactory.create_fastapi_app).__globals__
    monkeypatch.setitem(target, "FastAPI", lambda **kwargs: seen.update(kwargs) or object())
    FastApiAppFactory().create_fastapi_app(dataclasses.replace(FastApiSettings(), telemetry={"tracing": False}))
    assert seen["telemetry"] == {"tracing": False}


# FastAPI appends its exporter to the GLOBAL provider when the app starts; the
# global can be set once per process, so each scenario runs in its own interpreter.
_SCENARIO = """
    import dataclasses, os, sys
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:9"
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from pico_fastapi.config import FastApiSettings
    from pico_fastapi.factory import FastApiAppFactory
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(InMemorySpanExporter()))
    trace.set_tracer_provider(provider)
    settings = FastApiSettings() if sys.argv[1] == "default" else dataclasses.replace(FastApiSettings(), telemetry={})
    app = FastApiAppFactory().create_fastapi_app(settings)
    from fastapi.testclient import TestClient
    with TestClient(app):  # FastAPI wires its exporter at startup
        pass
    print(len(provider._active_span_processor._span_processors))
"""


def _processors_after_app(scenario):
    out = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(_SCENARIO), scenario], capture_output=True, text=True, check=True
    )
    return int(out.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(Version(fastapi.__version__) < Version("0.142"), reason="no built-in telemetry")
def test_default_settings_keep_fastapi_from_adding_a_second_otlp_exporter():
    pytest.importorskip("opentelemetry.sdk.trace")
    pytest.importorskip("opentelemetry.exporter.otlp.proto.http")  # fastapi[opentelemetry]
    # FastAPI's own default appends an OTLP exporter to the configured provider...
    assert _processors_after_app("fastapi-default") == 2
    # ...pico-fastapi's default setting prevents it.
    assert _processors_after_app("default") == 1
