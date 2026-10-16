import traceback
from dataclasses import dataclass, field

import substance_painter.layerstack as splayerstack
import substance_painter.logging as splog
import substance_painter.project as spproject
import substance_painter.textureset as sptextureset
import substance_painter.ui as spui

try:
    from PySide6 import QtCore, QtGui, QtWidgets

    QAction = QtGui.QAction

    splog.info("Loaded PySide6")
except Exception:
    from PySide2 import QtCore, QtGui, QtWidgets

    QAction = QtWidgets.QAction

    splog.info("Loaded PySide2")

VERSION = [0, 3, 1]
VERSION_STR = ".".join(str(v) for v in VERSION)

PLUGIN_NAME = "Quick Tools"
MENU_CATEGORY_0 = "Quick Tools"
ACTION_RENAME = "Rename Texture Sets..."
ACTION_TOGGLE = "Toggle Layers by Name..."

plugin_widgets = []


@dataclass
class ToggleLayersToolSettings:
    unchecked_texture_sets: set[str] = field(default_factory=set)
    on_names: str = ""
    off_names: str = ""
    loose_matching: bool = False


@dataclass
class Settings:
    """Session-only settings, kept in memory until Painter closes."""

    toggle_layers_tool: ToggleLayersToolSettings = field(default_factory=ToggleLayersToolSettings)


SessionSettings: Settings = Settings()


def get_texture_set_name(ts):
    # 11.0+: `name` is a property. Older versions: `name()` is a method.
    name = ts.name
    return name() if callable(name) else name


def can_rename_texture_sets(texture_sets):
    # In the old API `name` is callable and has no setter. Assigning to it
    # could silently shadow the method instead of raising, so check up front.
    return not any(callable(ts.name) for ts in texture_sets)


def rename_texture_sets(renames):
    if not can_rename_texture_sets([ts for ts, _ in renames]):
        raise RuntimeError("Renaming texture sets requires Substance 3D Painter 11.0 or newer.")

    # Two-pass rename through temporary names to allow swaps/chains (A->B, B->A)
    for i, (ts, _) in enumerate(renames):
        ts.name = f"__{PLUGIN_NAME.replace(' ', '_')}_tmp_{i}__"

    for ts, new_name in renames:
        ts.name = new_name


def parse_names(text):
    """'a, b ,, c' -> ['a', 'b', 'c'] (empty entries and case-insensitive duplicates removed)"""
    names, seen = [], set()

    for part in text.split(","):
        part: str = part.strip()
        key: str = part.casefold()
        if part and key not in seen:
            seen.add(key)
            names.append(part)

    return names


def find_node_state(key, states, loose):
    """Return True/False for the node name `key`, or None if nothing matches."""
    if key in states:  # Exact match
        return states[key]

    if not loose:
        return None

    matches = [k for k in states if key.startswith(k)]
    if not matches:
        return None

    # If several entries match, longer one wins
    return states[max(matches, key=len)]


def get_child_nodes(node):
    """Child noeds of a group layer, or [] for regular layers."""
    for attr in ("sub_layers", "children"):
        value = getattr(node, attr, None)
        if value is not None:
            return list(value() if callable(value) else value)

    getter = getattr(splayerstack, "get_children", None)
    if getter:
        try:
            return list(getter(node))
        except Exception:
            pass

    return []


def iter_nodes(nodes):
    """Depth-first walk over every layer/folder."""
    for node in nodes:
        yield node
        yield from iter_nodes(get_child_nodes(node))


def get_stacks(ts):
    try:
        return list(ts.all_stacks())
    except Exception:
        return [sptextureset.Stack.from_name(get_texture_set_name(ts))]


def apply_toggles(texture_sets, states, loose=False):
    """states: {name.casefold(): bool}. Returns number of nodes changed."""
    changed = 0

    for ts in texture_sets:
        for stack in get_stacks(ts):
            roots = splayerstack.get_root_layer_nodes(stack)
            for node in iter_nodes(roots):
                key = node.get_name().strip().casefold()
                state = find_node_state(key, states, loose)
                if state is None:
                    continue

                node.set_visible(state)
                changed += 1

    return changed


def show_rename_dialog():
    if not spproject.is_open():
        QtWidgets.QMessageBox.information(spui.get_main_window(), PLUGIN_NAME, "A project must first be open.")
        return

    texture_sets = sptextureset.all_texture_sets()
    if not texture_sets:
        QtWidgets.QMessageBox.information(spui.get_main_window(), PLUGIN_NAME, "Project has no texture sets.")
        return

    if not can_rename_texture_sets(texture_sets):
        QtWidgets.QMessageBox.warning(
            spui.get_main_window(),
            PLUGIN_NAME,
            "Renaming texture sets requires Substance 3D Painter 11.0 or newer.",
        )
        return

    try:
        dialog = RenameDialog(texture_sets, spui.get_main_window())
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        renames = dialog.get_renames()
        if not renames:
            return

        rename_texture_sets(renames)
        splog.info(f"{PLUGIN_NAME}: renamed {len(renames)} texture set(s)")
    except Exception as e:
        splog.error(f"{PLUGIN_NAME}: {traceback.format_exc()}")


def show_toggle_layers_dialog():
    main_window = spui.get_main_window()

    if not spproject.is_open():
        QtWidgets.QMessageBox.information(main_window, PLUGIN_NAME, "A project must be open.")
        return

    texture_sets = sptextureset.all_texture_sets()
    if not texture_sets:
        QtWidgets.QMessageBox.information(main_window, PLUGIN_NAME, "Project has no texture sets.")
        return

    try:
        dialog = ToggleLayersDialog(texture_sets, main_window)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        on_names = dialog.get_on_names()
        off_names = dialog.get_off_names()

        states = {n.casefold(): True for n in on_names}
        states.update({n.casefold(): False for n in off_names})

        # Names present in both lists -> Ask user
        off_keys = {n.casefold() for n in off_names}
        conflicts = [n for n in on_names if n.casefold() in off_keys]

        if conflicts:
            conflict_dialog = ConflictDialog(conflicts, main_window)
            if conflict_dialog.exec_() != QtWidgets.QDialog.Accepted:
                return

            for name, state in conflict_dialog.get_states().items():
                states[name.casefold()] = state

        changed = apply_toggles(dialog.get_selected_texture_sets(), states, dialog.is_loose_matching())
        splog.info(f"{PLUGIN_NAME}: toggled {changed} layer(s)/folder(s)")
    except Exception:
        splog.error(f"{PLUGIN_NAME}: {traceback.format_exc()}")


class RenameDialog(QtWidgets.QDialog):
    def __init__(self, texture_sets, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{PLUGIN_NAME} - {VERSION_STR}")
        self.setModal(True)
        # self.setGeometry(self.x(), self.y(), 300, self.height())
        self.setMinimumWidth(450)

        self._texture_sets = texture_sets
        self._edits = []  # (original_name, QLineEdit)

        self._setup_layout()

    def _setup_layout(self):
        splog.info("Setup layout")

        layout = QtWidgets.QVBoxLayout(self)

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._header("Original name"), 0, 0)
        grid.addWidget(self._header("New name"), 0, 1)

        for row, ts in enumerate(self._texture_sets, start=1):
            name = get_texture_set_name(ts)

            label = QtWidgets.QLabel(name)
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

            edit = QtWidgets.QLineEdit(name)

            grid.addWidget(label, row, 0)
            grid.addWidget(edit, row, 1)
            self._edits.append((name, edit))

        # Scroll area for overflow of Texture Sets
        container = QtWidgets.QWidget()
        container.setLayout(grid)
        scroll = CompactScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _header(text):
        label = QtWidgets.QLabel(f"<b>{text}</b>")
        return label

    def _on_accept(self):
        new_names = [edit.text().strip() for _, edit in self._edits]

        if any(not n for n in new_names):
            QtWidgets.QMessageBox.warning(self, PLUGIN_NAME, "Names cannot be empty.")
            return

        if len(set(new_names)) != len(new_names):
            QtWidgets.QMessageBox.warning(self, PLUGIN_NAME, "Each texture set requires a unique name.")
            return

        self.accept()

    def center(self):
        # Center the dialog on the parent's screen
        if not self.parent:
            return

        parent_geometry = self.parent.geometry()
        center_point = parent_geometry.center()
        self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)

    def get_renames(self):
        """Return a list of (TextureSet, new_name) for names that changed."""

        renames = []

        for ts, (original, edit) in zip(self._texture_sets, self._edits):
            new_name = edit.text().strip()
            if new_name != original:
                renames.append((ts, new_name))

        return renames


class CompactScrollArea(QtWidgets.QScrollArea):
    """Scroll area that prefers its minimum height instead of fitting its contents."""

    def sizeHint(self):
        return QtCore.QSize(super().sizeHint().width(), self.minimumHeight())


class ToggleLayersDialog(QtWidgets.QDialog):
    def __init__(self, texture_sets, parent=None):
        super().__init__(parent)
        self.tool_name = "ToggleLayersDialog"
        self.setWindowTitle(f"{PLUGIN_NAME} - {VERSION_STR}")
        self.setModal(True)
        self.setMinimumWidth(450)

        self._texture_sets = texture_sets
        self._checks = []  # (TextureSet, QLineEdit)

        self._setup_layout()

    def _setup_layout(self):
        splog.info("Setup layout")

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(QtWidgets.QLabel("<b>Texture Sets</b>"))

        # Select all/none
        row = QtWidgets.QHBoxLayout()
        btn_all = QtWidgets.QPushButton("All")
        btn_none = QtWidgets.QPushButton("None")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_none.clicked.connect(lambda: self._set_all(False))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        row.addStretch(1)
        layout.addLayout(row)

        # Scrollable checkbox list
        saved_unchecked = SessionSettings.toggle_layers_tool.unchecked_texture_sets

        list_layout = QtWidgets.QVBoxLayout()
        for ts in self._texture_sets:
            name = get_texture_set_name(ts)
            check = QtWidgets.QCheckBox(get_texture_set_name(ts))
            check.setChecked(name not in saved_unchecked)
            list_layout.addWidget(check)
            self._checks.append((ts, check))
        list_layout.addStretch(1)

        container = QtWidgets.QWidget()
        container.setLayout(list_layout)
        scroll = CompactScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Name fields
        form = QtWidgets.QFormLayout()
        self._on_edit = QtWidgets.QLineEdit()
        self._on_edit.setPlaceholderText("ex.: Dirt, scratches, Edge Wear")
        self._off_edit = QtWidgets.QLineEdit()
        self._off_edit.setPlaceholderText("ex.: Debug, reference")
        form.addRow("Toggle ON:", self._on_edit)
        form.addRow("Toggle OFF:", self._off_edit)
        layout.addLayout(form)

        # Loose checkbox for name matching
        self._loose_check = QtWidgets.QCheckBox("Loose matching (layer names starting with the entry)")
        self._loose_check.setToolTip('ex.: "dam" matches "Damage" and "Damge"')
        self._loose_check.setChecked(SessionSettings.toggle_layers_tool.loose_matching)
        layout.addWidget(self._loose_check)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self._on_reject)
        layout.addWidget(buttons)

    def _save_settings(self):
        splog.info(f"{self.tool_name}: saving settings")

        s = SessionSettings.toggle_layers_tool
        s.unchecked_texture_sets = {get_texture_set_name(ts) for ts, check in self._checks if not check.isChecked()}
        s.on_names = self._on_edit.text()
        s.off_names = self._off_edit.text()
        s.loose_matching = self._loose_check.isChecked()

    def _set_all(self, state):
        for _, check in self._checks:
            check.setChecked(state)

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
        return [ts for ts, check in self._checks if check.isChecked()]

    def get_on_names(self):
        return parse_names(self._on_edit.text())

    def get_off_names(self):
        return parse_names(self._off_edit.text())

    def is_loose_matching(self):
        return self._loose_check.isChecked()


class ConflictDialog(QtWidgets.QDialog):
    """Ask for final state of names that appear in both On and Off lists."""

    def __init__(self, names, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{PLUGIN_NAME} - Conflicting names")
        self.setModal(True)
        self.setMinimumWidth(350)

        self._checks = []  # (name, QCheckBox)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(
            QtWidgets.QLabel("These names were entered in both ON and OFF fields.\n" "Checked = ON, unchecked = OFF.")
        )

        list_layout = QtWidgets.QVBoxLayout()
        for name in names:
            check = QtWidgets.QCheckBox(name)
            check.setChecked(True)
            list_layout.addWidget(check)
            self._checks.append((name, check))
        list_layout.addStretch(1)

        container = QtWidgets.QWidget()
        container.setLayout(list_layout)
        scroll = CompactScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_states(self):
        """Return {name: bool} where True = ON."""
        return {name: check.isChecked() for name, check in self._checks}


def start_plugin():
    main_window = spui.get_main_window()

    # Add menu entry
    menu = main_window.menuBar().addMenu(MENU_CATEGORY_0)

    # Add "Rename" action
    action_rename_texture_sets = menu.addAction(ACTION_RENAME)
    action_rename_texture_sets.triggered.connect(show_rename_dialog)

    # Add "Toggle Layers" action
    action_toggle_layers = menu.addAction(ACTION_TOGGLE)
    action_toggle_layers.triggered.connect(show_toggle_layers_dialog)

    plugin_widgets.append(menu)

    splog.info(f"Started {PLUGIN_NAME} - {VERSION_STR}")


def close_plugin():
    for widget in plugin_widgets:
        try:
            spui.delete_ui_element(widget)
        except Exception as e:
            splog.error(f"Failed to delete UI element: {widget}: {e}")
    plugin_widgets.clear()

    splog.info(f"Closed {PLUGIN_NAME} - {VERSION_STR}")


if __name__ == "__main__":
    start_plugin()
