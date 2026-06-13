"""Plugins package for the getter service.

Plugins should live as separate modules under this package (e.g.
`app.plugins.json_plugin`). They will be discovered automatically by the
`PluginRegistry.discover` method; avoid importing concrete plugin modules
here so that discovery can import them dynamically.
"""

from app.plugins.base import FetcherPlugin

__all__ = ["FetcherPlugin"]
