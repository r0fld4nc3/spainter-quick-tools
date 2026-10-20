"""
Single place that decides between PySide6 (Painter 11+) and PySide2 (Painter 10).
"""

import substance_painter.logging as splog

from .constants import PLUGIN_NAME, VERSION_STR

try:
    from PySide6 import QtCore, QtGui, QtWidgets

    PYSIDE_VERSION = 6
except Exception:
    from PySide2 import QtCore, QtGui, QtWidgets

    PYSIDE_VERSION = 2

splog.info(f"{PLUGIN_NAME} - {VERSION_STR}: Loaded PySide{PYSIDE_VERSION}")

__all__ = ["QtCore", "QtGui", "QtWidgets", "PYSIDE_VERSION"]
