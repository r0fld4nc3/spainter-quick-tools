import substance_painter.logging as splog
import substance_painter.ui as spui

from ..constants import PLUGIN_NAME, VERSION_STR
from ..painter_utils import get_project_texture_sets, get_texture_set_name
from ..qt_compat import QtCore, QtWidgets
from ..widgets import CompactScrollArea, make_ok_cancel
from .base import Tool


def can_rename_texture_sets(texture_sets):
    # In the old API `name` is callable and has no setter. Assigning to it could silently shadow the method instead of raising.
    return not any(callable(ts.name) for ts in texture_sets)


def rename_texture_sets(renames):
    if not can_rename_texture_sets([ts for ts, _ in renames]):
        raise RuntimeError("Renaming texture sets requires Substance 3D Painter 11.0 or newer.")

    # Two-pass rename through temporary names to allow swaps/chains (A->B, B->A)
    for i, (ts, _) in enumerate(renames):
        ts.name = f"__{PLUGIN_NAME.replace(' ', '_')}_tmp_{i}__"

    for ts, new_name in renames:
        ts.name = new_name


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
        scroll.setMinimumHeight(150)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        layout.addWidget(make_ok_cancel(self._on_accept, self.reject))

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


class RenameTextureSetsTool(Tool):
    name = "Rename Texture Sets"
    menu_label = "Rename Texture Sets..."

    def run(self):
        texture_sets = get_project_texture_sets()
        if texture_sets is None:
            return

        main_window = spui.get_main_window()

        if not can_rename_texture_sets(texture_sets):
            QtWidgets.QMessageBox.warning(
                main_window,
                PLUGIN_NAME,
                "Renaming texture sets requires Substance 3D Painter 11.0 or newer.",
            )
            return

        dialog = RenameDialog(texture_sets, main_window)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        renames = dialog.get_renames()
        if not renames:
            return

        rename_texture_sets(renames)
        splog.info(f"{PLUGIN_NAME}: renamed {len(renames)} texture set(s)")
