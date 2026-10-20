import substance_painter.logging as splog
import substance_painter.ui as spui

from ..constants import PLUGIN_NAME, VERSION_STR
from ..qt_compat import QtCore, QtGui, QtWidgets
from ..updater import fetch_latest_release
from .base import Tool


def open_release_page(release):
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(release.url))


class CheckForUpdatesTool(Tool):
    name = "Check for Updates"
    menu_label = "Check for Updates..."

    def run(self):
        main_window = spui.get_main_window()

        # Manual check. Short blocking request
        release, error = None, ""
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        try:
            release = fetch_latest_release()
        except Exception as e:
            error = str(e)
            splog.error(error)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        if error:
            QtWidgets.QMessageBox.warning(main_window, PLUGIN_NAME, f"Could not fetch updates.\n\n{error}")
            return

        if not release.is_newer:
            QtWidgets.QMessageBox.information(
                main_window,
                PLUGIN_NAME,
                f"Already sporting latest release ({VERSION_STR}).",
            )
            return

        answer = QtWidgets.QMessageBox.question(
            main_window,
            PLUGIN_NAME,
            f"A newer version is available: {release.tag}\nInstalled: {VERSION_STR}\n\nOpen release page?",
        )
        if answer == QtWidgets.QMessageBox.Yes:
            open_release_page(release)
