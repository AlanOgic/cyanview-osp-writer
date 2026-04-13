"""cyanview-osp-writer — MCP server for Cyanview draft review with OSP methodology."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cyanview-osp-writer")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"
