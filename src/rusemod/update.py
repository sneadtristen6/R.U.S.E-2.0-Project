"""Updating the installed apps from GitHub Releases (PLAN.md decision 10): both apps ask for their newest release on
start, and offer it; Update downloads its installer, checks it, and runs it silently, and the app starts again.

- **Which release:** the newest one whose tag is `<app>-v<major.minor.patch>` (launcher-v0.2.0, studio-v0.5.0), or
  with a fourth number for a small fix (studio-v0.9.4.1: TAG_VERSION), newer than the running version. Drafts never
  count; the Studio's releases are pre-releases (a preview) and count. Apps from before 0.9.4 / 0.4.4 see only
  three-number tags.
- **Which file:** the release's `RUSE-<App>-Setup-<version>.exe`.
- **Checked before it runs:** its SHA-256 must equal what GitHub reports for the file (the asset's `digest`) and the
  one our release notes publish (.github/workflows/release.yml writes it); at least one must be there, and both must
  agree. A file that doesn't match is deleted. Downloads come only from this repo's releases, over HTTPS.
- **Installing:** the installer runs with /SILENT (no questions, for this Windows user, no admin rights), the app
  quits, the installer replaces it and starts it again (installers/installer.iss).
- Only an installed app updates itself; from the repo (`py -3 -m ...`) the answer is "update with git pull".
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = "sneadtristen6/R.U.S.E-2.0-Project"
API = f"https://api.github.com/repos/{REPO}/releases?per_page=40"
APPS = {"launcher": "Launcher", "studio": "Studio"}
_TIMEOUT = 15
_ALLOWED_HOSTS = ("https://github.com/", "https://objects.githubusercontent.com/",
                  "https://release-assets.githubusercontent.com/", "https://api.github.com/")


class UpdateError(Exception):
    """An update that can't go ahead, with a message for the player."""


@dataclass
class Release:
    app: str
    version: str
    tag: str
    page: str            # the release's page (what's new)
    asset: str           # the installer's file name
    url: str             # its download address
    size: int
    sha256: str          # the checked-against hash (lowercase hex)
    changes: list = None  # before and after, per version newer than the running one (changes_since)


ROW = re.compile(r"^\s*\|(.+?)\|(.+?)\|\s*$")


def changes_since(body: str, current: str, newest: str) -> list[dict]:
    """What changes between the running version and `newest`, from a release's notes (`body`, every version's notes,
    newest first: `**0.8.1:** ...`): for each version after `current` up to `newest`, the rows of its before/after
    table (`| Before | Now |`), or, with no table, its bullets as "now" with nothing before. [{version, before, now}],
    newest first."""
    parts = re.split(r"^\*\*(\d+\.\d+\.\d+):\*\*", body or "", flags=re.M)
    out = []
    for version, text in zip(parts[1::2], parts[2::2]):
        if not version_tuple(current) < version_tuple(version) <= version_tuple(newest):
            continue
        rows = []
        for line in text.splitlines():
            m = ROW.match(line)
            if not m:
                continue
            before, now = m.group(1).strip(), m.group(2).strip()
            if set(before) <= set("-: ") or before.lower() == "before":
                continue  # the header and its rule
            rows.append({"version": version, "before": before, "now": now})
        if not rows:
            first = text.strip().splitlines()[0].strip() if text.strip() else ""
            bullets = [ln.strip()[2:] for ln in text.splitlines() if ln.startswith("- ")]
            rows = [{"version": version, "before": "", "now": b} for b in (bullets or [first]) if b]
        out += rows
    return out


TAG_VERSION = r"\d+\.\d+\.\d+(?:\.\d+)?"  # a release tag's version: three numbers, or four for a small fix (0.9.4.1)


def version_tuple(v: str) -> tuple:
    try:
        return tuple(int(p) for p in str(v).split("."))
    except ValueError:
        return (0,)


def installed_app() -> bool:
    """True in the installed program (Nuitka sets __compiled__ in every module it compiles), False from the repo."""
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


# Each app's installer id (installers/build_app.py: they never change, so a new installer replaces the old version).
APP_IDS = {"launcher": "96F731B1-F85A-48E8-A810-49128DF99706", "studio": "89731BD4-5E55-415F-970E-F6CBBB8CFD51"}
UNINSTALL = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"


def fix_app_list_version(app: str, version: str, reg=None) -> str | None:
    """Windows' list of installed apps shows the version the installer wrote. On the owner's PC it still said the
    Launcher was 0.1.0 when 0.3.1 was installed (issue #15): the installer writes it on every install, so an old entry
    written somewhere else (an install made from inside another app's sandbox, 2026-09-28) was shown instead. The
    installed app sets its own entry's version when it differs. Returns the old version when it changed one, else None;
    never raises (a list entry isn't worth failing a start for). `reg` is winreg (tests pass a stand-in)."""
    try:
        if reg is None:
            import winreg as reg
        key = rf"{UNINSTALL}\{{{APP_IDS[app]}}}_is1"
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_READ | reg.KEY_SET_VALUE) as k:
            try:
                old = reg.QueryValueEx(k, "DisplayVersion")[0]
            except OSError:
                old = None
            if old == version:
                return None
            reg.SetValueEx(k, "DisplayVersion", 0, reg.REG_SZ, version)
            return old or ""
    except (OSError, ImportError, KeyError):
        return None


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "RUSE-Mod-Platform-updater"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:  # noqa: S310 (https only, fixed host)
        return json.loads(r.read().decode("utf-8"))


FEED = f"https://github.com/{REPO}/releases.atom"


def _get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "RUSE-Mod-Platform-updater"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:  # noqa: S310 (https only, fixed host)
        return r.read().decode("utf-8")


def feed_releases(text: str) -> list[dict]:
    """The releases in GitHub's release feed (`FEED`), shaped like the API's answer: tag_name, html_url, body (the
    notes, with the installer's SHA-256 our release workflow writes), and each app's installer as an asset at its
    download address (no size, no GitHub digest: the notes' SHA-256 is then the check). The feed has no drafts.
    It's the fallback when the API refuses: GitHub allows 60 API calls an hour per internet address, shared by every
    program on it; the feed has no such limit."""
    import html
    out = []
    for entry in text.split("<entry>")[1:]:
        link = re.search(r'<link[^>]*href="([^"]+)"', entry)
        content = re.search(r"<content[^>]*>(.*?)</content>", entry, re.S)
        if not link or not link.group(1).startswith(f"https://github.com/{REPO}/releases/tag/"):
            continue
        tag = link.group(1).rsplit("/", 1)[-1]
        m = re.match(rf"^(launcher|studio)-v({TAG_VERSION})$", tag)
        assets = []
        if m:
            name = f"RUSE-{APPS[m.group(1)]}-Setup-{m.group(2)}.exe"
            assets.append({"name": name, "browser_download_url": f"https://github.com/{REPO}/releases/download/{tag}/{name}",
                           "size": 0})
        out.append({"tag_name": tag, "html_url": link.group(1), "draft": False, "assets": assets,
                    "body": html.unescape(content.group(1)) if content else ""})
    return out


def latest(app: str, current: str, fetch=_get_json, fetch_text=_get_text) -> Release | None:
    """The newest release of `app` newer than `current`, or None. Asked once when the app starts. Raises UpdateError
    when GitHub can't be asked (neither its API nor its release feed) or the release can't be checked."""
    if app not in APPS:
        raise ValueError(app)
    try:
        releases = fetch(API)
    except (OSError, ValueError) as exc:  # refused (the hourly limit) or unreachable: the release feed instead
        try:
            releases = feed_releases(fetch_text(FEED))
        except (OSError, ValueError):
            raise UpdateError(f"GitHub couldn't be reached to look for updates ({exc}).") from None
    tag_re = re.compile(rf"^{app}-v({TAG_VERSION})$")
    best = None
    for rel in releases if isinstance(releases, list) else []:
        m = tag_re.match(str(rel.get("tag_name", "")))
        if not m or rel.get("draft"):
            continue
        if best is None or version_tuple(m.group(1)) > version_tuple(best[0]):
            best = (m.group(1), rel)
    if best is None or version_tuple(best[0]) <= version_tuple(current):
        return None
    version, rel = best
    name = f"RUSE-{APPS[app]}-Setup-{version}.exe"
    asset = next((a for a in rel.get("assets", []) if a.get("name") == name), None)
    if asset is None:
        raise UpdateError(f"{APPS[app]} {version} is out, but its installer ({name}) isn't in the release yet.")
    url = str(asset.get("browser_download_url", ""))
    if not url.startswith("https://github.com/"):
        raise UpdateError(f"{name}'s download address isn't on GitHub, so it isn't used.")
    hashes = set()
    digest = str(asset.get("digest") or "")
    if digest.startswith("sha256:"):
        hashes.add(digest[7:].lower())
    notes = re.findall(r"\b[0-9a-fA-F]{64}\b", str(rel.get("body") or ""))
    if notes:
        hashes.add(notes[0].lower())
    if len(hashes) != 1:
        raise UpdateError(f"{APPS[app]} {version} can't be checked (its SHA-256 is missing or differs between GitHub "
                          f"and the release notes), so it isn't installed.")
    return Release(app, version, rel["tag_name"], str(rel.get("html_url", "")), name, url, int(asset.get("size", 0)),
                   hashes.pop(), changes_since(str(rel.get("body") or ""), current, version))


def _open(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "RUSE-Mod-Platform-updater"})
    resp = urllib.request.urlopen(req, timeout=60)  # noqa: S310
    final = resp.geturl()
    if not final.startswith(_ALLOWED_HOSTS):
        resp.close()
        raise UpdateError(f"the download went to {final.split('/')[2]}, which isn't GitHub; stopped.")
    return resp


def download(rel: Release, folder: Path, progress=lambda done, total: None, opener=_open) -> Path:
    """Download the installer into `folder`, checking its SHA-256 as it comes. Returns its path."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / rel.asset
    part = target.with_suffix(".part")
    h = hashlib.sha256()
    done = 0
    try:
        with opener(rel.url) as resp, part.open("wb") as f:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                progress(done, rel.size)
    except UpdateError:
        part.unlink(missing_ok=True)
        raise
    except OSError as exc:
        part.unlink(missing_ok=True)
        raise UpdateError(f"the download stopped ({exc}).") from None
    if h.hexdigest() != rel.sha256:
        part.unlink(missing_ok=True)
        raise UpdateError("the downloaded installer isn't the published one (its SHA-256 differs), so it was deleted.")
    os.replace(part, target)
    return target


def _quit_soon(seconds: float = 1.0) -> None:
    import threading
    import time
    threading.Thread(target=lambda: (time.sleep(seconds), os._exit(0)), daemon=True).start()


class UpdateCalls:
    """The window API's update calls, for both apps (a mixin: the API sets UPDATE_APP and UPDATE_VERSION and has
    `_home` and `_jobs`). Tests replace `_update_fetch`, `_update_fetch_text`, `_update_opener`, `_update_popen` and
    `_update_quit`."""

    UPDATE_APP = ""
    UPDATE_VERSION = "0.0.0"
    _update_fetch = staticmethod(_get_json)
    _update_fetch_text = staticmethod(_get_text)
    _update_opener = staticmethod(_open)
    _update_popen = staticmethod(subprocess.Popen)
    _update_quit = staticmethod(_quit_soon)
    _update_installed = staticmethod(installed_app)
    _update_found: Release | None = None

    def app_version(self) -> dict:
        """This app and the version running, shown beside its name."""
        return {"app": APPS.get(self.UPDATE_APP, ""), "version": self.UPDATE_VERSION}

    def update_check(self) -> dict:
        """Is there a newer release of this app? {"available", "version", "current" (the running one), "changes"
        (before and after, per version since the running one: changes_since), "page", "size", "installed" (False
        when running from the repo), "error"}. Asked once per start."""
        try:
            rel = latest(self.UPDATE_APP, self.UPDATE_VERSION, fetch=self._update_fetch, fetch_text=self._update_fetch_text)
        except UpdateError as exc:
            return {"available": False, "error": str(exc), "current": self.UPDATE_VERSION}
        self._update_found = rel
        if rel is None:
            return {"available": False, "version": self.UPDATE_VERSION, "current": self.UPDATE_VERSION}
        return {"available": True, "version": rel.version, "current": self.UPDATE_VERSION, "changes": rel.changes or [],
                "page": rel.page, "size": rel.size, "installed": bool(self._update_installed())}

    def update_page(self) -> dict:
        """Open the newer release's page (what's new) in the browser."""
        from .play import open_url
        rel = self._update_found
        if rel is None or not rel.page.startswith(f"https://github.com/{REPO}/"):
            raise UpdateError("There's no release page to open.")
        (getattr(self, "_update_open_url", None) or open_url)(rel.page)
        return {"opened": rel.page}

    def update_install(self) -> dict:
        """Download the newer installer, check it, run it silently and quit (the installer starts the app again).
        Returns {"job": id}; the job's lines say how far the download is."""
        from .webui import Job
        rel = self._update_found
        if rel is None:
            raise UpdateError("There's no update to install (look again after starting the app).")
        if not self._update_installed():
            raise UpdateError("This copy runs from the repo, not from an installer: update it with git pull.")
        job = Job()
        self._jobs[job.id] = job

        def work(say):
            last = [-1]

            def progress(done, total):
                pct = int(done * 100 / total) if total else 0
                if pct // 10 != last[0]:
                    last[0] = pct // 10
                    say(f"{pct}%")
            path = download(rel, Path(self._home) / "updates", progress, opener=self._update_opener)
            say("installing")
            run_installer(path, popen=self._update_popen)
            self._update_quit()
        return job.start(work, f"{APPS[self.UPDATE_APP]} {rel.version} is installing; it opens again by itself.",
                         plain=(UpdateError,))


def run_installer(path: Path, popen=subprocess.Popen) -> None:
    """Start the checked installer silently, apart from this app (which then quits so its files can be replaced)."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    popen([str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/relaunch=1"],
          close_fds=True, creationflags=flags)
