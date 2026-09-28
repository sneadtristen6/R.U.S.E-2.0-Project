"""The platform's own folder: settings, mod sets and caches such as the game index. Never inside the game folder.

Windows: %LOCALAPPDATA%\\RUSE Mod Platform. Elsewhere: ~/.local/share/ruse-mod-platform. $RUSE_PLATFORM_HOME overrides.
"""
from __future__ import annotations

import os
from pathlib import Path


def default_home() -> Path:
    if os.environ.get("RUSE_PLATFORM_HOME"):
        return Path(os.environ["RUSE_PLATFORM_HOME"])
    if os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "RUSE Mod Platform"
    return Path.home() / ".local" / "share" / "ruse-mod-platform"
