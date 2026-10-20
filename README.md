# Quick Tools for Substance 3D Painter

A small Python plugin for Adobe Substance 3D Painter that adds quick, dialog-based helpers for repetitive Texture Set chores. Tools appear under a **Quick Tools** menu in the Painter menu bar.

## Tools

### Rename Texture Sets...

Batch rename Texture Sets from a single dialog.

- Lists every Texture Set in the project with an editable "New name" field.
- Rejects empty names and duplicate names.
- Supports swaps and chains (e.g. `A -> B` and `B -> A`) by renaming through temporary names.
- Requires **Substance 3D Painter 11.0 or newer** (older versions don't allow renaming Texture Sets from Python).

### Toggle Layers by Name...

Turn layers and folders on or off by name across multiple Texture Sets at once.

1. Check the Texture Sets you want to affect (all are checked by default; use **All** / **None** for quick selection).
2. Enter a comma-separated list of layer/folder names to toggle **ON**.
3. Enter a comma-separated list of layer/folder names to toggle **OFF**.
4. Click **OK**.

For each selected Texture Set, every layer and folder in the stack (including nested ones) whose name matches an entry is shown or hidden accordingly.

Notes:

- Matching is case-insensitive and ignores leading/trailing spaces (`dirt` matches `Dirt`).
- If the same name appears in both lists, a conflict dialog lets you choose the final state for each one (checked = ON, unchecked = OFF).
- The number of toggled layers/folders is written to the Painter log.

## Installation

1. Copy the plugin folder into your Painter Python plugins folder:
   - **Windows:** `%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins`
   - **macOS:** `~/Documents/Adobe/Adobe Substance 3D Painter/python/plugins`
   - **Linux:** `~/.local/share/Adobe/Adobe Substance 3D Painter/python/plugins`
2. Restart Painter, or use **Python > Reload Plugins Folder**.
3. Enable the plugin from the **Python** menu.
4. Open a project. The tools are available under **Quick Tools**.

## Requirements

- Adobe Substance 3D Painter (11.0+ for Rename Texture Sets)
- A project must be open to use either tool