from fastapi import FastAPI


def test_settings_title_version_debug(app: FastAPI):
    assert app.title == "Integration Test API"
    assert app.version == "9.9.9"
    assert app.debug is True
