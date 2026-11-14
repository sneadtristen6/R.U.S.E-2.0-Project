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
- **Required updates** (the owner, 2026-10-30: "a box it can't skip ... a feature that we can have for certain
  updates, like 1.0 ... it should update by itself without asking"): a version whose notes have the line
  `<!-- required update -->` under its `**x.y.z:**` line (the English notes, .github/release-notes/<app>.md; GitHub
  doesn't show the line) is required: an app older than it shows a box it can't close and installs the newest
  release by itself (ui/required.js), and Play and Test in game stay off until it has (rusemod.play.Starter.required).
  The app keeps the required version in settings.json, where only it writes, so a start without the internet stays
  blocked.
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

from . import net
from .home import save_settings, settings
from .mod_index import plain

REPO = "sneadtristen6/R.U.S.E-2.0-Project"
API = f"https://api.github.com/repos/{REPO}/releases?per_page=40"
APPS = {"launcher": "Launcher", "studio": "Studio"}
_TIMEOUT = 15
_ALLOWED_HOSTS = ("https://github.com/", "https://objects.githubusercontent.com/",
                  "https://release-assets.githubusercontent.com/", "https://api.github.com/")


class UpdateError(Exception):
    """An update that can't go ahead, with a message for the player. `why`, when given: why GitHub couldn't be reached,
    in plain words (rusemod.mod_index.plain), said in the player's language inside the message (words)."""

    def __init__(self, *args, why: str = ""):
        super().__init__(*args)
        self.why = why


# the refusals of the calls both apps share, said in the player's language by words() (both apps' page_error)
SHARED_REFUSALS = ("UpdateError", "BackupError", "OwnedPassError")


def words(exc: Exception, lang: str) -> str:
    """A refusal of the updates, a backup's or the sign-in's (UpdateError, BackupError, OwnedPassError) in `lang`, from
    rusemod/buildtext.toml (buildtext.ENDS lists them), why GitHub couldn't be reached said in it too; as it is when
    no entry says it (the plain-words job, 2026-11-14: "GitHub couldn't be reached to look for updates (<urlopen error
    [WinError 10061] ...>)", English in both apps in every language)."""
    from . import buildtext
    said = buildtext.worded(str(exc), lang)
    why = getattr(exc, "why", "")
    if why and why in said:
        said = said.replace(why, buildtext.worded(why, lang), 1)
    return said


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
    notes_url: str = ""   # every language's notes (NOTES_ASSET), when the release has them
    required: str = ""    # the newest required version newer than the running one (required_since), or ""


# Every language's release notes, published beside the installer (.github/workflows/release.yml, installers/
# notes_json.py): {language code: the notes in it, written as the English ones are}. The apps show the changes in
# their own language, and in English for a language that has none (the owner, 2026-10-05: the update panel was in
# English in a French player's Studio).
NOTES_ASSET = "RUSE-{app}-notes.json"
NOTES_MAX = 2_000_000

ROW = re.compile(r"^\s*\|(.+?)\|(.+?)\|\s*$")


def _rule(line: str) -> bool:
    """A table's rule (|---|---|)."""
    m = ROW.match(line)
    return bool(m) and set(m.group(1).strip()) <= set("-: ")


def changes_since(body: str, current: str, newest: str) -> list[dict]:
    """What changes between the running version and `newest`, from a release's notes (`body`, every version's notes,
    newest first: `**0.8.1:** ...`, or `**0.9.8.1:** ...` with a fourth number): for each version after `current` up
    to `newest`, the rows of its before/after table (`| Before | Now |`), or, with no table, its bullets as "now" with
    nothing before. [{version, before, now}], newest first."""
    parts = re.split(rf"^\*\*({TAG_VERSION}):\*\*", body or "", flags=re.M)
    out = []
    for version, text in zip(parts[1::2], parts[2::2]):
        if not version_tuple(current) < version_tuple(version) <= version_tuple(newest):
            continue
        rows = []
        lines = text.splitlines()
        for i, line in enumerate(lines):
            m = ROW.match(line)
            if not m:
                continue
            before, now = m.group(1).strip(), m.group(2).strip()
            if (_rule(line) or before.lower() == "before" or (i + 1 < len(lines) and _rule(lines[i + 1]))):
                continue  # the header (in any language: the row over the rule) and its rule
            rows.append({"version": version, "before": before, "now": now})
        if not rows:
            first = text.strip().splitlines()[0].strip() if text.strip() else ""
            bullets = [ln.strip()[2:] for ln in text.splitlines() if ln.startswith("- ")]
            rows = [{"version": version, "before": "", "now": b} for b in (bullets or [first]) if b]
        out += rows
    return out


TAG_VERSION = r"\d+\.\d+\.\d+(?:\.\d+)?"  # a release's version: three numbers, or four (0.9.4.1, 0.9.8.1)
REQUIRED = re.compile(r"^\s*<!--\s*required update\s*-->\s*$", re.M | re.I)  # under a version's line: it's required


def required_since(body: str, current: str) -> str | None:
    """The newest version after `current` whose notes (in a release's `body`, every version's, as changes_since
    reads them) carry the required-update line, or None."""
    parts = re.split(rf"^\*\*({TAG_VERSION}):\*\*", body or "", flags=re.M)
    found = [v for v, text in zip(parts[1::2], parts[2::2])
             if version_tuple(v) > version_tuple(current) and REQUIRED.search(text)]
    return max(found, key=version_tuple) if found else None


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
    with net.urlopen(req, _TIMEOUT) as r:  # noqa: S310 (https only, fixed host)
        return json.loads(r.read().decode("utf-8"))


FEED = f"https://github.com/{REPO}/releases.atom"


def _get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "RUSE-Mod-Platform-updater"})
    with net.urlopen(req, _TIMEOUT) as r:  # noqa: S310 (https only, fixed host)
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
            book = NOTES_ASSET.format(app=APPS[m.group(1)])  # (an older release hasn't one: English then)
            assets.append({"name": book, "browser_download_url": f"https://github.com/{REPO}/releases/download/{tag}/{book}",
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
            why = plain(exc)   # (never Python's or Windows' own words)
            raise UpdateError(f"GitHub couldn't be reached to look for updates ({why}).", why=why) from None
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
    book = next((a for a in rel.get("assets", []) if a.get("name") == NOTES_ASSET.format(app=APPS[app])), None)
    book_url = str((book or {}).get("browser_download_url", ""))
    body = str(rel.get("body") or "")
    return Release(app, version, rel["tag_name"], str(rel.get("html_url", "")), name, url, int(asset.get("size", 0)),
                   hashes.pop(), changes_since(body, current, version),
                   book_url if book_url.startswith("https://github.com/") else "", required_since(body, current) or "")


def changes_in(rel: Release, lang: str, current: str, opener=None) -> list:
    """The release's changes since `current` in language `lang` (the apps' codes: fr, ger, ...), from its notes asset
    (NOTES_ASSET, downloaded from GitHub only); the English ones (rel.changes) for English, for a language the notes
    haven't got, or when they can't be had."""
    if not lang or lang in ("us", "base") or not rel.notes_url:
        return rel.changes or []
    try:
        with (opener or _open)(rel.notes_url) as resp:
            data = resp.read(NOTES_MAX + 1)
        if len(data) > NOTES_MAX:
            return rel.changes or []
        text = json.loads(data.decode("utf-8-sig")).get(lang)
    except (UpdateError, OSError, ValueError, AttributeError):
        return rel.changes or []
    local = changes_since(text, current, rel.version) if isinstance(text, str) else []
    mine = {r["version"] for r in local}
    # version by version: in the language where its notes have that version, else in English (someone two versions
    # behind sees both, the older one in English when it was never translated)
    out, done = [], set()
    for r in rel.changes or []:
        v = r["version"]
        if v not in mine:
            out.append(r)
        elif v not in done:
            out += [x for x in local if x["version"] == v]
            done.add(v)
    return out or local


def _open(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "RUSE-Mod-Platform-updater"})
    resp = net.urlopen(req, 60)  # noqa: S310
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
        why = plain(exc)
        raise UpdateError(f"the download stopped ({why}).", why=why) from None
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

    def use_required_updates(self) -> None:
        """Play and Test in game wait for a required update (each app's app.py turns it on; tests of made-up games
        don't meet it)."""
        self._starter.required = self._update_refusal

    def _update_kept(self) -> str:
        """The required version this app last saw, while it's newer than the running one, else "" (settings.json
        "required_update", which only the app writes: the window can't take it off)."""
        kept = settings(Path(self._home)).get("required_update")
        version = kept.get(self.UPDATE_APP, "") if isinstance(kept, dict) else ""
        return version if isinstance(version, str) and version_tuple(version) > version_tuple(self.UPDATE_VERSION) else ""

    def _update_keep(self, version: str) -> None:
        values = settings(Path(self._home))
        kept = values.get("required_update") if isinstance(values.get("required_update"), dict) else {}
        if kept.get(self.UPDATE_APP, "") == version:
            return
        if version:
            kept[self.UPDATE_APP] = version
        else:
            kept.pop(self.UPDATE_APP, None)
        values["required_update"] = kept
        save_settings(Path(self._home), values)

    def _update_refusal(self) -> str | None:
        """For rusemod.play.Starter: the message when a required update must go in first, else None."""
        if not ((self._update_found.required if self._update_found else "") or self._update_kept()):
            return None
        lang = (self.prefs() or {}).get("lang") or "us"
        said = self.strings(lang).get("update_required_refused") or "{app} has a required update to install first."
        return said.replace("{app}", f"RUSE {APPS[self.UPDATE_APP]}")

    def app_version(self) -> dict:
        """This app and the version running, shown beside its name."""
        return {"app": APPS.get(self.UPDATE_APP, ""), "version": self.UPDATE_VERSION}

    def update_check(self, lang: str = "us") -> dict:
        """Is there a newer release of this app? {"available", "version", "current" (the running one), "changes"
        (before and after, per version since the running one: changes_since; in `lang` when the release's notes
        have it: changes_in), "page", "size", "installed" (False when running from the repo), "error", "required"
        (it must go in: the window installs it by itself and can't be used meanwhile), "offline" (a required update
        seen before, GitHub unreachable now)}. Asked once per start, and again when the language changes."""
        try:
            rel = latest(self.UPDATE_APP, self.UPDATE_VERSION, fetch=self._update_fetch, fetch_text=self._update_fetch_text)
        except UpdateError as exc:
            kept = self._update_kept()
            prefs = getattr(self, "prefs", None)   # (asked without a language: the window's own)
            said_in = lang if lang not in ("", "us") or prefs is None else (prefs().get("lang") or "us")
            return {"available": False, "error": words(exc, said_in), "current": self.UPDATE_VERSION,
                    **({"required": True, "offline": True, "version": kept} if kept else {})}
        self._update_found = rel
        self._update_keep(rel.required if rel is not None else "")
        if rel is None:
            return {"available": False, "version": self.UPDATE_VERSION, "current": self.UPDATE_VERSION}
        changes = changes_in(rel, lang, self.UPDATE_VERSION, opener=self._update_opener)
        if getattr(self, "_update_offered", None) != rel.version:  # Bug Watch: once per version offered, per run
            self._update_offered = rel.version
            from . import bugwatch
            bugwatch.count("updates", "offered")
        return {"available": True, "version": rel.version, "current": self.UPDATE_VERSION, "changes": changes,
                "page": rel.page, "size": rel.size, "installed": bool(self._update_installed()),
                "required": bool(rel.required)}

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
            from . import bugwatch
            try:
                path = download(rel, Path(self._home) / "updates", progress, opener=self._update_opener)
                say("installing")
                run_installer(path, popen=self._update_popen)
            except Exception:
                bugwatch.count("updates", "failed")
                raise
            # Bug Watch: "installed" is the checked installer started (the app quits for it); kept now, since the
            # quit (os._exit) skips the save Bug Watch leaves for the app's end
            bugwatch.count("updates", "installed")
            watch = bugwatch.current()
            if watch is not None:
                watch.save()
            self._update_quit()
        return job.start(work, f"{APPS[self.UPDATE_APP]} {rel.version} is installing; it opens again by itself.",
                         plain=(UpdateError,))


def run_installer(path: Path, popen=subprocess.Popen) -> None:
    """Start the checked installer silently, apart from this app (which then quits so its files can be replaced)."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    popen([str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/relaunch=1"],
          close_fds=True, creationflags=flags)
