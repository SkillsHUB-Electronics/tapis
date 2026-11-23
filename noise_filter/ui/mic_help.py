"""Explain an audio device problem and offer the Windows settings page that fixes it."""
from __future__ import annotations

import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets as W

from ..audio.errors import AudioError, PRIVACY_URL
from ..i18n import tr


def _fmt(key: str, err: AudioError, lang: str) -> str:
    s = tr(key, lang).format(side=tr(f"mic.side.{err.side or 'input'}", lang))
    return s[:1].upper() + s[1:]


def message(err: AudioError, lang: str) -> str:
    """The user-facing explanation (no technical detail)."""
    return _fmt(f"mic.err.{err.reason}", err, lang)


def short(err: AudioError, lang: str) -> str:
    """One line for the status bar / tray."""
    return _fmt(f"mic.short.{err.reason}", err, lang)


def open_settings(url: str) -> None:
    if not url:
        return
    if sys.platform == "win32":
        try:
            os.startfile(url)                   # ms-settings: URIs open the Settings app
            return
        except OSError:
            pass
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


def show(parent, err: AudioError, lang: str) -> None:
    """Modal explanation with a button that opens the right Settings page."""
    t = lambda k: tr(k, lang)
    box = W.QMessageBox(parent)
    box.setIcon(W.QMessageBox.Warning)
    box.setWindowTitle(t("mic.title"))
    box.setText(message(err, lang))
    if err.detail:
        box.setDetailedText(err.detail)
    fix = None
    if err.settings_url:
        fix = box.addButton(t("mic.open_privacy" if err.settings_url == PRIVACY_URL else "mic.open_sound"),
                            W.QMessageBox.AcceptRole)
    box.addButton(W.QMessageBox.Close)
    box.exec()
    if fix is not None and box.clickedButton() is fix:
        open_settings(err.settings_url)
