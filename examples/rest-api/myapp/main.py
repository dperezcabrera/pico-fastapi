from pico_boot import init
from pico_ioc import configuration, YamlTreeSource
from fastapi import FastAPI


def create_app() -> FastAPI:
    config = configuration(YamlTreeSource("application.yaml"))

    container = init(
        modules=[
            "myapp.config",
            "myapp.services",
            "myapp.controllers",
        ],
        config=config,
    )

    return container.get(FastAPI)


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
