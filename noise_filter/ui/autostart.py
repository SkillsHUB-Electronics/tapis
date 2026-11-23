"""'Start with Windows': a value under HKCU\\...\\Run (per user, no admin rights needed).

The registry is the source of truth, so the checkbox also reflects a change made in
Task Manager > Startup apps. The installer removes the value on uninstall.
"""
import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "Tapis"
LEGACY_VALUE = "NoiseFilter"     # name used before the app was renamed to Tapis (0.11.0)


def supported() -> bool:
    return sys.platform == "win32"


def command() -> str:
    """Command line Windows runs at sign-in: open hidden in the tray."""
    if getattr(sys, "frozen", False):                      # installed Tapis.exe
        return f'"{sys.executable}" ui --minimized'
    exe = sys.executable
    w = os.path.join(os.path.dirname(exe), "pythonw.exe")   # no console window
    return f'"{w if os.path.isfile(w) else exe}" -m noise_filter.cli ui --minimized'


def _winreg():
    import winreg
    return winreg


def _has(name: str) -> bool:
    reg = _winreg()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY) as k:
            reg.QueryValueEx(k, name)
        return True
    except OSError:
        return False


def is_enabled() -> bool:
    return supported() and (_has(VALUE) or _has(LEGACY_VALUE))


def set_enabled(on: bool) -> None:
    if not supported():
        return
    reg = _winreg()
    with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_SET_VALUE) as k:
        if on:
            reg.SetValueEx(k, VALUE, 0, reg.REG_SZ, command())
        names = (LEGACY_VALUE,) if on else (VALUE, LEGACY_VALUE)
        for name in names:
            try:
                reg.DeleteValue(k, name)
            except FileNotFoundError:
                pass


def refresh() -> None:
    """Keep the path current when the app was reinstalled elsewhere or updated, and move an
    entry written by an older "Noise Filter" version to the new name."""
    if is_enabled():
        try:
            set_enabled(True)
        except OSError:
            pass
