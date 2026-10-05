"""Help and bug reports, for both apps: the wiki (the field manual), Discussions, and a bug report opened in the
browser with the app, its version and the message filled in. Nothing is ever sent from the apps: the player reads
the report and posts it themselves on GitHub.

A message can hold paths, and paths hold the Windows user name (C:\\Users\\<name>\\...): the report shortens them to
%LOCALAPPDATA% / %USERPROFILE% first, so a public post never shows who the player is on their PC.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlencode

from .mod_index import PAGE as MOD_LIST_PAGE

REPO_URL = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project"
LINKS = {"wiki": f"{REPO_URL}/wiki", "discussions": f"{REPO_URL}/discussions",
         "help": f"{REPO_URL}/discussions/categories/help",
         "mods": MOD_LIST_PAGE,  # the supported-mods list (MOD_FORMAT §15): see it, or add a mod to it
         "guidelines": f"{MOD_LIST_PAGE}/blob/main/GUIDELINES.md"}  # what the list accepts
BUG_CATEGORY = "bug-reports"      # the category's slug: .github/DISCUSSION_TEMPLATE/bug-reports.yml is its form
APP_NAMES = {"studio": "RUSE Studio", "launcher": "RUSE Launcher"}  # as the form's "Which app?" lists them
MESSAGE_MOST = 1500               # characters of a message that go into the link (a long URL gets refused)
_USERS = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+[^\\/\s]+")  # C:\Users\<name>, any drive, either slash


def private_paths_out(text: str) -> str:
    """`text` with the player's own folders written the way Windows names them for anyone: %LOCALAPPDATA%,
    %APPDATA%, %USERPROFILE%, then any other C:\\Users\\<name> left."""
    out = str(text or "")
    for var in ("LOCALAPPDATA", "APPDATA", "USERPROFILE"):
        value = os.environ.get(var) or (str(Path.home()) if var == "USERPROFILE" else "")
        if value:
            for form in {value, value.replace("\\", "/")}:
                out = re.sub(re.escape(form), f"%{var}%", out, flags=re.IGNORECASE)
    return _USERS.sub("%USERPROFILE%", out)


def report_url(app: str, version: str, message: str = "") -> str:
    """A new bug report in Discussions: the category, a title naming the app, its version and the message's first
    line, and the form's own boxes (app, version, message) filled in where GitHub takes them from the link."""
    name = APP_NAMES.get(app, app)
    message = private_paths_out(message).strip()
    first = message.splitlines()[0] if message else ""
    title = f"[Bug] {name} {version}" + (f": {first[:80]}" if first else ": ")
    fields = {"category": BUG_CATEGORY, "title": title, "app": name, "version": version}
    if message:
        fields["message"] = message[:MESSAGE_MOST]
    return f"{REPO_URL}/discussions/new?{urlencode(fields)}"


class CommunityCalls:
    """The window API's help calls, for both apps (a mixin beside rusemod.update.UpdateCalls, whose UPDATE_APP,
    UPDATE_VERSION and `_update_open_url` it uses)."""

    def help_links(self) -> dict:
        """The wiki's and Discussions' addresses, for the window to show."""
        return dict(LINKS)

    def open_help(self, what: str) -> dict:
        """Open the wiki ("wiki"), Discussions ("discussions"), its Help category ("help") or the supported-mods
        list's page ("mods") in the browser."""
        if what not in LINKS:
            raise ValueError(f"There's no help page called {what!r}")
        return self._community_open(LINKS[what])

    def report_problem(self, message: str = "") -> dict:
        """Open a new bug report in the browser, the app, its version and `message` (an error the window showed)
        filled in. Returns {"opened": the address}."""
        return self._community_open(report_url(self.UPDATE_APP, self.UPDATE_VERSION, message))

    def _community_open(self, url: str) -> dict:
        from .play import open_url
        (getattr(self, "_update_open_url", None) or open_url)(url)
        return {"opened": url}
