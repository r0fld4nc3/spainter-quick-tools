"""
Quick Tools for Substance Painter 3D.

Init entry point for the plugin.
"""

import sys

import substance_painter.logging as splog
import substance_painter.ui as spui

from .constants import CHECK_FOR_UPDATES_ON_STARTUP, MENU_NAME, PLUGIN_NAME, VERSION_STR
from .qt_compat import QtWidgets
from .tools import ALL_TOOLS, UTILITY_TOOLS
from .tools.check_for_updates import open_release_page
from .updater import UpdateChecker

plugin_widgets = []
active_tools = []
update_checker = None


def _add_tools(menu, tool_classes):
    for tool_cls in tool_classes:
        tool = tool_cls()
        action = menu.addAction(tool.menu_label)
        action.triggered.connect(tool.run_safe)
        active_tools.append(tool)


def _start_update_check(menu):
    """
    Check GitHub in the background. If a newer release exists, flag it in the menu.
    """
    global update_checker

    def on_finished(release, error):
        if error:
            splog.warning(f"{PLUGIN_NAME}: update check failed: {error}")
            return

        if not release.is_newer:
            splog.info(f"{PLUGIN_NAME}: up to date: {VERSION_STR}")
            return

        splog.info(f"{PLUGIN_NAME}: update available: {release.tag} (installed {VERSION_STR}) - {release.url}")

        try:
            menu.setTitle(f"{MENU_NAME} (Update available)")
            menu.addSeparator()
            action = menu.addAction(f"Get {release.tag}...")
            action.triggered.connect(lambda *_: open_release_page(release))
        except RuntimeError:
            # Menu may no longer exist.
            splog.warning(f"{PLUGIN_NAME}: could not show update notice in menu")

    update_checker = UpdateChecker(on_finished)
    update_checker.start()


def start_plugin():
    main_window = spui.get_main_window()

    """
    # Menu is owned by the menu bar; actions are owned by the menu
    menu = main_window.menuBar().addMenu(MENU_NAME)
    """

    menu = QtWidgets.QMenu(MENU_NAME, main_window)
    spui.add_menu(menu)

    _add_tools(menu, ALL_TOOLS)
    menu.addSeparator()
    _add_tools(menu, UTILITY_TOOLS)

    # Only the menu is tracked. Deleting it deletes its actions too
    plugin_widgets.append(menu)

    if CHECK_FOR_UPDATES_ON_STARTUP:
        _start_update_check(menu)

    splog.info(f"Started {PLUGIN_NAME} - {VERSION_STR}")


def close_plugin():
    global update_checker

    # Menu about to be deleted. Ensure late update result doesn't touch it
    if update_checker:
        update_checker.cancel()
        update_checker = None

    for widget in plugin_widgets:
        try:
            spui.delete_ui_element(widget)
        except Exception as e:
            splog.error(f"Failed to delete UI element: {widget}: {e}")

    plugin_widgets.clear()
    active_tools.clear()

    _unload_submodules()

    splog.info(f"Closed {PLUGIN_NAME} - {VERSION_STR}")


def _unload_submodules():
    """Forget this plugin's submodules so the next start re-imports them from disk.

    Without this, reloading the plugin in Painter only re-runs __init__.py and keeps
    old versions of tools/, text_utils.py, etc. in memory until Painter restarts.
    Annoying.
    """
    prefix = __name__ + "."
    for name in [m for m in sys.modules if m.startswith(prefix)]:
        del sys.modules[name]
