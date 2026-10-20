import substance_painter.logging as splog
import substance_painter.ui as spui

from ..constants import PLUGIN_NAME, VERSION_STR
from ..painter_utils import (
    get_project_texture_sets,
    get_texture_set_name,
    iter_layer_nodes,
)
from ..qt_compat import QtWidgets
from ..settings import SessionSettings
from ..text_utils import find_matching_key, parse_names
from ..widgets import CheckList, TextureSetPicker, make_ok_cancel
from .base import Tool


def apply_toggles(texture_sets, states, loose=False):
    """states: {name.casefold(): bool}. Returns number of nodes changed."""
    changed = 0
    log = []

    for ts, node in iter_layer_nodes(texture_sets):
        node_name = node.get_name()
        match = find_matching_key(node_name.strip().casefold(), states, loose)
        if match is None:
            continue

        state = states[match]
        node.set_visible(state)
        log.append(f"[{get_texture_set_name(ts)}] {node_name} set visible: {state}")
        changed += 1

    splog.info("\n".join(log))
    return changed


class ToggleLayersDialog(QtWidgets.QDialog):
    def __init__(self, texture_sets, parent=None):
        super().__init__(parent)
        self.tool_name = "ToggleLayersDialog"
        self.setWindowTitle(f"{PLUGIN_NAME} - {VERSION_STR}")
        self.setModal(True)
        self.setMinimumWidth(450)

        self._texture_sets = texture_sets

        self._setup_layout()

    def _setup_layout(self):
        layout = QtWidgets.QVBoxLayout(self)
        settings = SessionSettings.toggle_layers_tool

        self._ts_picker = TextureSetPicker(self._texture_sets, settings.unchecked_texture_sets)
        layout.addWidget(self._ts_picker)

        # Name fields
        form = QtWidgets.QFormLayout()
        self._on_edit = QtWidgets.QLineEdit(settings.on_names)
        self._on_edit.setPlaceholderText("ex.: Dirt, scratches, Edge Wear")
        self._off_edit = QtWidgets.QLineEdit(settings.off_names)
        self._off_edit.setPlaceholderText("ex.: Debug, reference")
        form.addRow("Toggle ON:", self._on_edit)
        form.addRow("Toggle OFF:", self._off_edit)
        layout.addLayout(form)

        # Loose checkbox for name matching
        self._loose_check = QtWidgets.QCheckBox("Loose matching (entry matches the start of any word)")
        self._loose_check.setToolTip('ex.: "summer" matches "CP - Summer", "dam" matches "Damage" and "Damge"')
        self._loose_check.setChecked(settings.loose_matching)
        layout.addWidget(self._loose_check)

        layout.addWidget(make_ok_cancel(self._on_accept, self._on_reject))

    def _save_settings(self):
        splog.info(f"{self.tool_name}: saving settings")

        s = SessionSettings.toggle_layers_tool
        s.unchecked_texture_sets = self._ts_picker.unchecked_names()
        # s.on_names = self._on_edit.text()
        # s.off_names = self._off_edit.text()
        s.loose_matching = self._loose_check.isChecked()

    def _on_accept(self):
        if not self.get_selected_texture_sets():
            QtWidgets.QMessageBox.warning(self, PLUGIN_NAME, "Select at least one texture set.")
            return

        if not self.get_on_names() and not self.get_off_names():
            QtWidgets.QMessageBox.warning(self, PLUGIN_NAME, "Enter at least one layer/folder name.")
            return

        self._save_settings()
        self.accept()

    def _on_reject(self):
        self._save_settings()
        self.reject()

    def get_selected_texture_sets(self):
        return self._ts_picker.selected_texture_sets()

    def get_on_names(self):
        return parse_names(self._on_edit.text())

    def get_off_names(self):
        return parse_names(self._off_edit.text())

    def is_loose_matching(self):
        return self._loose_check.isChecked()


class ConflictDialog(QtWidgets.QDialog):
    """
    Ask for final state of names that appear in both On and Off lists.
    """

    def __init__(self, names, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{PLUGIN_NAME} - Conflicting names")
        self.setModal(True)
        self.setMinimumWidth(350)

        self._names = names

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(
            QtWidgets.QLabel("These names were entered in both ON and OFF fields.\n" "Checked = ON, unchecked = OFF.")
        )

        self._list = CheckList(min_height=100)
        for name in names:
            self._list.add_item(name, name)
        layout.addWidget(self._list)

        layout.addWidget(make_ok_cancel(self.accept, self.reject))

    def get_states(self):
        """
        Return {name: bool} where True = ON.
        """
        on = set(self._list.checked_payloads())
        return {name: name in on for name in self._names}


class ToggleLayersTool(Tool):
    name = "Toggle Layers"
    menu_label = "Toggle Layers by Name..."

    def run(self):
        texture_sets = get_project_texture_sets()
        if texture_sets is None:
            return

        main_window = spui.get_main_window()

        dialog = ToggleLayersDialog(texture_sets, main_window)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        on_names = dialog.get_on_names()
        off_names = dialog.get_off_names()

        splog.info(f"On Names: {on_names}")
        splog.info(f"Off Names: {off_names}")

        states = {n.casefold(): True for n in on_names}
        states.update({n.casefold(): False for n in off_names})

        splog.info(f"States: {states}")

        # Names present in both lists -> Ask user
        off_keys = {n.casefold() for n in off_names}
        conflicts = [n for n in on_names if n.casefold() in off_keys]

        splog.info(f"Conflicts ({len(conflicts)}): {conflicts}")

        if conflicts:
            conflict_dialog = ConflictDialog(conflicts, main_window)
            if conflict_dialog.exec_() != QtWidgets.QDialog.Accepted:
                return

            for name, state in conflict_dialog.get_states().items():
                states[name.casefold()] = state

        changed = apply_toggles(dialog.get_selected_texture_sets(), states, dialog.is_loose_matching())
        splog.info(f"{PLUGIN_NAME}: toggled {changed} layer(s)/folder(s)")
