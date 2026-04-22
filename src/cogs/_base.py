from __future__ import annotations

import importlib
import importlib.resources
import pkgutil
import sys

from discord.ext import commands


class AutoCog(commands.Cog):
    _registry: list[type] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        AutoCog._registry.append(cls)

    @classmethod
    def load_all(cls) -> None:
        package = importlib.import_module(__package__)
        for module_info in pkgutil.walk_packages(
            path=package.__path__,
            prefix=package.__name__ + ".",
            onerror=lambda _: None
        ):
            if not module_info.ispkg and module_info.name not in sys.modules:
                importlib.import_module(module_info.name)

    @classmethod
    def get_registry(cls) -> list[type]:
        cls.load_all()
        return cls._registry