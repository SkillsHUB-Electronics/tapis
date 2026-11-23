"""Per-user data folder: %APPDATA%\\Tapis (settings, downloaded models, sample-sharing state).

The app was called "Noise Filter" before 0.11.0 and kept its data in %APPDATA%\\NoiseFilter. The first
call moves that folder to the new name, so people who update keep their settings, models and
installation ID. If the move fails (for example a file is locked), the old folder is used as it is.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_DIR = "Tapis"
LEGACY_DIR = "NoiseFilter"


def _base() -> Path:
    return Path(os.environ.get("APPDATA") or str(Path.home() / ".config"))


def data_dir() -> Path:
    base = _base()
    new, old = base / APP_DIR, base / LEGACY_DIR
    if new.exists() or not old.is_dir():
        return new
    try:
        old.rename(new)
        return new
    except OSError:
        pass
    try:
        shutil.copytree(old, new)
        return new
    except OSError:
        shutil.rmtree(new, ignore_errors=True)
        return old
