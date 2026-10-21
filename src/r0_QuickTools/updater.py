"""
Checks GitHub for a newer release of the plugin.

Uses the GitHub REST API (`/releases/latest`), which returns JSON with the release tag and page URL.
Drafts and pre-releases are excluded by GitHub. Nothing is written to disk.
"""

import json
import re
import threading
import urllib.request
from dataclasses import dataclass

from .constants import (
    GITHUB_API_LATEST_RELEASE,
    PLUGIN_NAME,
    REQUEST_TIMEOUT,
    VERSION,
    VERSION_STR,
)
from .qt_compat import QtCore


@dataclass
class ReleaseInfo:
    tag: str  # Tag as written on GitHub: "v0.4.0"
    version: tuple  # Parsed tag: (0, 4, 0)
    url: str  # Release page

    @property
    def is_newer(self) -> bool:
        """
        True if release is newer than installed version.
        """
        return is_newer(self.version, tuple(VERSION))


def parse_version(tag) -> tuple[int]:
    """
    v0.4.0 -> (0, 4, 0). Also handles '0.4', 'v1.2.3-beta', 'release1.2'.
    """
    match = re.search(r"\d+(?:\.\d+)*", tag)
    if not match:
        raise ValueError(f"Unrecognised version tag: {tag!r}")

    return tuple(int(n) for n in match.group().split("."))


def is_newer(remote, local) -> bool:
    """
    Compare version tuples, treating missing parts as 0 so (0, 5) == (0, 5, 0).
    """
    length = max(len(remote), len(local))
    remote = tuple(remote) + (0,) * (length - len(remote))
    local = tuple(local) + (0,) * (length - len(local))

    return remote > local


def fetch_latest_release() -> ReleaseInfo:
    """
    Blocking request to GitHub.
    Returns ReleaseInfo or raises network/API errors.
    """

    request = urllib.request.Request(
        GITHUB_API_LATEST_RELEASE,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{PLUGIN_NAME.replace(' ', '')}/{VERSION_STR}",
        },
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        data = json.load(response)

    tag = data["tag_name"]
    return ReleaseInfo(tag=tag, version=parse_version(tag), url=data["html_url"])


class UpdateChecker(QtCore.QObject):
    """
    Runs fetch_latest_release() on a background thread to prevent Painter's UI to freeze
    then calls `on_finished(release, error)` back to the UI Thread.

    release: ReleaseInfo or None if check failed
    error: '' on success otherwise short error message
    """

    _finished = QtCore.Signal(object, str)

    def __init__(self, on_finished, parent=None):
        super().__init__(parent)
        self._on_finished = on_finished

        # Queued: worker thread emits, slot always runs on the UI Thread
        self._finished.connect(self._deliver, QtCore.Qt.QueuedConnection)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def cancel(self):
        self._on_finished = None

    def _run(self):
        # Worker thread: No Qt widgets or Painter API calls here please
        try:
            release, error = fetch_latest_release(), ""
        except Exception as e:
            release, error = None, str(e)

        try:
            self._finished.emit(release, error)
        except RuntimeError:
            pass

    @QtCore.Slot(object, str)
    def _deliver(self, release, error):
        if self._on_finished:
            self._on_finished(release, error)
