"""
Tool registry. To add a tool: create a module in this folder and add its class to ALL_TOOLS.
"""

from .check_for_updates import CheckForUpdatesTool
from .rename_texture_sets import RenameTextureSetsTool
from .toggle_layers import ToggleLayersTool

ALL_TOOLS = [
    RenameTextureSetsTool,
    ToggleLayersTool,
]

UTILITY_TOOLS = [
    CheckForUpdatesTool,
]
