"""Single source of truth for the package version.

The version is declared only in ``pyproject.toml``'s ``[project]`` section.
At runtime it is resolved from the installed package metadata via
``importlib.metadata.version("p4mcp-server")``. Resolution raises
``PackageNotFoundError`` — and we fall back to ``"0.0.0"`` — whenever that
distribution name is not present in the environment's metadata: a bare source
checkout (package never installed) or a name mismatch (installed under a
different distribution name, e.g. a renamed local wheel).

The build scripts (``build.sh`` / ``build.bat``) bake the static
``pyproject.toml`` version into this file before freezing the PyInstaller
binary, then restore this importlib.metadata form afterwards.
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("p4mcp-server")
except PackageNotFoundError:
    __version__ = "0.0.0"
