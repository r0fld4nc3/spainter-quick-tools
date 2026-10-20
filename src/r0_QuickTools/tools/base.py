import traceback

import substance_painter.logging as splog

from ..constants import PLUGIN_NAME


class Tool:
    """
    Base class for a tool that appears as an entry in the plugin menu.
    """

    name: str = ""  # Primarily for logging
    menu_label: str = ""  # Text shown in menu

    def run(self):
        raise NotImplementedError

    def run_safe(self, *_):
        """
        Menu entry point: runs the tool and logs exceptions instead of raising to Painter.
        """
        try:
            self.run()
        except Exception:
            splog.error(f"{PLUGIN_NAME} - {self.name}: {traceback.format_exc()}")
