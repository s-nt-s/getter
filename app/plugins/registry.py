from typing import Type
from app.plugins.base import FetcherPlugin
import logging
from importlib import import_module
from pkgutil import iter_modules
from inspect import isclass

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry of plugins that can handle different URL patterns."""

    def __init__(self) -> None:
        self.__plugins: tuple[Type[FetcherPlugin]] = self.__discover()
        content_type: set[str] = set()
        for p in self.__plugins:
            for c in p.content_type:
                content_type.add(c)
        self.content_type = tuple(sorted(content_type))

    def find(self, url: str, content_type: str) -> Type[FetcherPlugin]:
        for plugin in self.__plugins:
            if plugin.is_for_me(url, content_type):
                return plugin
        raise LookupError(f"No plugin matched URL: {url}")

    def __discover(self, package: str = "app.plugins"):
        """Import all modules in `package` and register plugin classes.

        Skips internal modules named 'base', 'registry' and '__init__'.
        """
        pkg = import_module(package)
        if not hasattr(pkg, "__path__"):
            return tuple()

        plugins: list[Type[FetcherPlugin]] = []
        skip = {"base", "registry", "__init__"}
        for finder, name, ispkg in iter_modules(pkg.__path__):
            if name in skip:
                continue
            module_name = f"{package}.{name}"
            try:
                module = import_module(module_name)
            except Exception as exc:
                logger.critical("Skipping plugin module %s: import failed: %s", module_name, exc)
                continue

            for obj in module.__dict__.values():
                if (
                    isclass(obj)
                    and issubclass(obj, FetcherPlugin)
                    and obj is not FetcherPlugin
                ):
                    plugins.append(obj)
                    logger.info("Registered plugin %s from module %s", getattr(obj, "name", repr(obj)), module_name)
        return tuple(plugins)
