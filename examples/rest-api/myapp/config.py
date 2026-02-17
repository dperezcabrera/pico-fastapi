from dataclasses import dataclass

from pico_ioc import configured


@configured(target="self", prefix="greeting", mapping="tree")
@dataclass
class GreetingConfig:
    default_language: str = "en"
