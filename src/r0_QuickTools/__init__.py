"""
Quick Tools for Substance Painter 3D.

Init entry point for the plugin.
"""

import substance_painter.logging as splog
import substance_painter.ui as spui

from .constants import MENU_NAME, PLUGIN_NAME, VERSION_STR
from .tools import ALL_TOOLS

plugin_widgets = []
active_tools = []


def start_plugin():
    main_window = spui.get_main_window()

    # Menu is owned by the menu bar; actions are owned by the menu
    menu = main_window.menuBar().addMenu(MENU_NAME)

    for tool_cls in ALL_TOOLS:
        tool = tool_cls()
        action = menu.addAction(tool.menu_label)
        action.triggered.connect(tool.run_safe)
        active_tools.append(tool)

    # Only the menu is tracked. Deleting it deletes its actions too
    plugin_widgets.append(menu)

    splog.info(f"Started {PLUGIN_NAME} - {VERSION_STR}")


def close_plugin():
    for widget in plugin_widgets:
        try:
            spui.delete_ui_element(widget)
        except Exception as e:
            splog.error(f"Failed to delete UI element: {widget}: {e}")

    plugin_widgets.clear()
    active_tools.clear()

    splog.info(f"Closed {PLUGIN_NAME} - {VERSION_STR}")
