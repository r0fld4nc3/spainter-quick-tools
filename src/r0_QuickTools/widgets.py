from .painter_utils import get_texture_set_name
from .qt_compat import QtCore, QtWidgets


class CompactScrollArea(QtWidgets.QScrollArea):
    """
    Scroll area that prefers its minimum height instead of fitting its contents.
    """

    def sizeHint(self):
        return QtCore.QSize(super().sizeHint().width(), self.minimumHeight())


class CheckList(CompactScrollArea):
    """
    Scrollable list of checkboxes, each carrying a payload object.
    """

    def __init__(self, parent=None, min_height=150):
        super().__init__(parent)
        self._checks = []  # (payload, QCheckBox)

        self._list_layout = QtWidgets.QVBoxLayout()
        self._list_layout.addStretch(1)

        container = QtWidgets.QWidget()
        container.setLayout(self._list_layout)

        self.setWidgetResizable(True)
        self.setMinimumHeight(min_height)
        self.setWidget(container)

    def add_item(self, label, payload=None, checked=True):
        check = QtWidgets.QCheckBox(label)
        check.setChecked(checked)
        # Insert before the trailing stretch
        self._list_layout.insertWidget(self._list_layout.count() - 1, check)
        self._checks.append((payload, check))
        return check

    def set_all(self, state):
        for _, check in self._checks:
            check.setChecked(state)

    def checked_payloads(self):
        return [payload for payload, check in self._checks if check.isChecked()]

    def unchecked_payloads(self):
        return [payload for payload, check in self._checks if not check.isChecked()]


class TextureSetPicker(QtWidgets.QWidget):
    """
    'Texture Sets' header, All/None buttons and a scrollable checkbox list.
    """

    def __init__(self, texture_sets, unchecked_names=(), parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QLabel("<b>Texture Sets</b>"))

        self._list = CheckList()
        for ts in texture_sets:
            name = get_texture_set_name(ts)
            self._list.add_item(name, ts, checked=name not in unchecked_names)

        row = QtWidgets.QHBoxLayout()
        btn_all = QtWidgets.QPushButton("All")
        btn_none = QtWidgets.QPushButton("None")
        btn_all.clicked.connect(lambda: self._list.set_all(True))
        btn_none.clicked.connect(lambda: self._list.set_all(False))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        row.addStretch(1)

        layout.addLayout(row)
        layout.addWidget(self._list)

    def selected_texture_sets(self):
        return self._list.checked_payloads()

    def unchecked_names(self):
        return {get_texture_set_name(ts) for ts in self._list.unchecked_payloads()}


def make_ok_cancel(on_accept, on_reject):
    """
    OK/Cancel button box, repeated in every dialog.
    """
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(on_reject)
    return buttons
