import substance_painter.layerstack as splayerstack
import substance_painter.project as spproject
import substance_painter.textureset as sptextureset
import substance_painter.ui as spui

from .constants import PLUGIN_NAME
from .qt_compat import QtWidgets


def get_texture_set_name(ts):
    # 11.0+: `name` is a property. Older versions: `name()` is a method.
    name = ts.name
    return name() if callable(name) else name


def get_stacks(ts):
    try:
        return list(ts.all_stacks())
    except Exception:
        return [sptextureset.Stack.from_name(get_texture_set_name(ts))]


def get_project_texture_sets():
    """
    Return the project's texture sets, or None if a tool can't run.
    """
    main_window = spui.get_main_window()

    if not spproject.is_open():
        QtWidgets.QMessageBox.information(main_window, PLUGIN_NAME, "A project must first be open.")
        return None

    texture_sets = sptextureset.all_texture_sets()
    if not texture_sets:
        QtWidgets.QMessageBox.information(main_window, PLUGIN_NAME, "Project has no texture sets.")
        return None

    return texture_sets


def get_child_nodes(node):
    """
    Child noeds of a group layer, or [] for regular layers.
    """
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
    """
    Depth-first walk over every layer/folder.
    """
    for node in nodes:
        yield node
        yield from iter_nodes(get_child_nodes(node))


def iter_layer_nodes(texture_sets):
    """
    Yield (texture_set, node) for every layer/folder in every stack of the given texture sets.
    """
    for ts in texture_sets:
        for stack in get_stacks(ts):
            for node in iter_nodes(splayerstack.get_root_layer_nodes(stack)):
                yield ts, node
