from typing import Protocol
from fastapi import FastAPI
from dataclasses import dataclass
from pico_ioc import configured

class FastApiConfigurer(Protocol):
    @property
    def priority(self) -> int:
        return 0

    def configure(self, app: FastAPI) -> None: ...

@configured(target="self", prefix="fastapi", mapping="tree")
@dataclass
class FastApiSettings:
    title: str = "Pico-FastAPI App"
    version: str = "1.0.0"
    debug: bool = False
