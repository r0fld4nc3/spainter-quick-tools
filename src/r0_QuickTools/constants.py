VERSION = [0, 4, 0]
VERSION_STR = ".".join(str(v) for v in VERSION)

PLUGIN_NAME = "Quick Tools"
MENU_NAME = "Quick Tools"

# Updater
GITHUB_OWNER = "r0fld4nc3"
GITHUB_REPO = "sppainter-quick-tools"
GITHUB_API_LATEST_RELEASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
CHECK_FOR_UPDATES_ON_STARTUP = True
REQUEST_TIMEOUT = 5  # seconds
