"""Updating the installed apps from GitHub Releases (PLAN.md decision 10): both apps ask for their newest release on
start, and offer it; Update downloads its installer, checks it, and runs it silently, and the app starts again.

- **Which release:** the newest one whose tag is `<app>-v<major.minor.patch>` (launcher-v0.2.0, studio-v0.5.0), or
  with a fourth number for a small fix (studio-v0.9.4.1: TAG_VERSION), newer than the running version, that carries
  the owner's signature (rusemod.releasesig: the legal fixes' Part 7, his decision 26 A of 2026-11-25). Up to
  CANDIDATES newer releases are looked at, newest first; one without a signature that fits is skipped and named, so it
  can't hold back a signed one below it. Drafts never count; the Studio's releases are pre-releases (a preview) and
  count. Apps from before 0.9.4 / 0.4.4 see only three-number tags.
- **Which file:** the release's `RUSE-<App>-Setup-<version>.exe`, at the address the app makes itself from this repo
  and the tag.
- **Checked before it runs:** its size and SHA-256 must be the ones the owner signed: a different file is refused
  before it's downloaded when GitHub's own listing already shows it, and deleted when the bytes that came differ. What
  GitHub says alone (its digest, the hash in the release text, the text's required line) is not trusted any more.
- **When it can't be confirmed as ours** (no signature that fits, or a file that isn't the one signed: his words of
  2026-11-25, "an update not signed by him points to his Discord"): nothing installs, the app says so, and its button
  opens our Discord. When a confirmed one fails to download (a cut-off, no connection, a server's error), each failed
  try is kept, and after TRIES of them the app stops trying by itself and points to the release page (his "after a few
  failed tries, stop retrying and point to the release page"); a required update keeps its block meanwhile.
- **Installing:** the installer runs with /SILENT (no questions, for this Windows user, no admin rights), the app
  quits, the installer replaces it and starts it again (installers/installer.iss).
- Only an installed app updates itself; from the repo (`py -3 -m ...`) the answer is "update with git pull".
- **Required updates** (the owner, 2026-10-30: "a box it can't skip ... a feature that we can have for certain
  updates, like 1.0 ... it should update by itself without asking"): a version whose English notes have the line
  `<!-- required update -->` under its `**x.y.z:**` line is required; the owner's signed statement carries that as a
  threshold (apps older than it install the release by themselves: releasesig.required_for), and only the signed
  threshold counts. An app older than it shows a box it can't close and installs the release by itself
  (ui/required.js), and Play and Test in game stay off until it has (rusemod.play.Starter.required). The app keeps the
  signed threshold in settings.json ("required_signed", where only it writes), so a start without the internet stays
  blocked. When GitHub answers and no signed statement requires a newer version, the kept one is cleared, as before.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import net, releasesig
from .home import save_settings, settings
from .mod_index import plain
from .releasesig import REQUIRED, TAG_VERSION, version_tuple  # noqa: F401  (REQUIRED: the notes' line, kept here)

REPO = "sneadtristen6/R.U.S.E-2.0-Project"
API = f"https://api.github.com/repos/{REPO}/releases?per_page=40"
APPS = {"launcher": "Launcher", "studio": "Studio"}
_TIMEOUT = 15
_ALLOWED_HOSTS = ("https://github.com/", "https://objects.githubusercontent.com/",
                  "https://release-assets.githubusercontent.com/", "https://api.github.com/")
DOWNLOADS = f"https://github.com/{REPO}/releases/download/"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
CANDIDATES = 5   # newer releases looked at, newest first, for one with a signature that fits
TRIES = 3        # failed downloads of one update before the app stops trying by itself (the owner's "a few")


class UpdateError(Exception):
    """An update that can't go ahead, with a message for the player. `why`, when given: why GitHub couldn't be reached,
    in plain words (rusemod.mod_index.plain), said in the player's language inside the message (words). `final`: the
    release isn't ours as signed (no signature that fits, or another file), so trying again won't help; else it
    couldn't be done now (no connection, a cut-off). `version`: the release it is about, when there is one. (One
    class, so both apps' page_error still says it in the player's language: SHARED_REFUSALS goes by the class name.)"""

    def __init__(self, *args, why: str = "", final: bool = False, version: str = ""):
        super().__init__(*args)
        self.why, self.final, self.version = why, final, version


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
    page: str            # the release's page (what's new), made from REPO and the tag
    asset: str           # the installer's file name
    url: str             # its download address, made from REPO and the tag
    size: int            # its size and SHA-256 as the owner signed them
    sha256: str
    changes: list = None  # before and after, per version newer than the running one (changes_in)
    notes_url: str = ""   # every language's notes (NOTES_ASSET), as signed:
    required: str = ""    # the signed threshold when the running version is older than it (releasesig.required_for)
    notes_size: int = 0
    notes_sha256: str = ""
    key: str = ""         # the release key that signed it
    commit: str = ""
    ignored: list = field(default_factory=list)  # newer versions skipped: no signature of ours that fits
    refused: str = ""     # GitHub's listing shows another installer than the signed one (why), else ""


# Every language's release notes, published beside the installer (.github/workflows/release.yml, installers/
# notes_json.py): {language code: the notes in it, written as the English ones are; English as "us"}. The apps show
# the changes in their own language, and in English for a language that has none (the owner, 2026-10-05: the update
# panel was in English in a French player's Studio). Its size and SHA-256 are in the signed statement: What's new
# comes from this checked file only, never from the release text.
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


def _get_sig(url: str):
    """A release's signature file (at most releasesig.MOST bytes, from GitHub only): its bytes, or None when the
    release has none (GitHub answers 404). Raises UpdateError (not final) when it can't be had now."""
    try:
        with _open(url) as resp:
            return resp.read(releasesig.MOST + 1)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        why = plain(exc)
        raise UpdateError(f"the signature couldn't be downloaded now ({why}).", why=why) from None
    except UpdateError:
        raise
    except OSError as exc:
        why = plain(exc)
        raise UpdateError(f"the signature couldn't be downloaded now ({why}).", why=why) from None
    except http.client.HTTPException:
        raise UpdateError("the signature couldn't be downloaded now (the connection was cut).") from None


def feed_releases(text: str) -> list[dict]:
    """The releases in GitHub's release feed (`FEED`), shaped like the API's answer: tag_name, html_url, body, and
    each app's installer, notes and signature as assets at their download addresses (no size, no GitHub digest: the
    signed size and SHA-256 are then checked on the download itself). The feed has no drafts. It's the fallback when
    the API refuses: GitHub allows 60 API calls an hour per internet address, shared by every program on it; the feed
    has no such limit."""
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
            for each in (name, NOTES_ASSET.format(app=APPS[m.group(1)]), name + releasesig.SUFFIX):
                assets.append({"name": each, "browser_download_url": f"{DOWNLOADS}{tag}/{each}", "size": 0})
        out.append({"tag_name": tag, "html_url": link.group(1), "draft": False, "assets": assets,
                    "body": html.unescape(content.group(1)) if content else "", "feed": True})
    return out


def latest(app: str, current: str, fetch=_get_json, fetch_text=_get_text, *, fetch_sig) -> Release | None:
    """The newest release of `app` newer than `current` whose signed statement fits it, or None when GitHub lists no
    newer release at all. Asked once when the app starts. Raises UpdateError (not final) when GitHub can't be asked now
    (neither its API nor its release feed, or a signature can't be had), and UpdateError (final, `version` the newest
    one) when newer releases are there but none carries a signature of ours that fits. A signed one whose installer, as
    GitHub lists it, isn't the signed one comes back with `refused` saying so (nothing of it installs)."""
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
    newer = []
    for rel in releases if isinstance(releases, list) else []:
        m = tag_re.match(str(rel.get("tag_name", ""))) if isinstance(rel, dict) else None
        if m and not rel.get("draft") and version_tuple(m.group(1)) > version_tuple(current):
            newer.append((version_tuple(m.group(1)), m.group(1), rel))
    if not newer:
        return None
    newer.sort(key=lambda found: found[0], reverse=True)
    ignored = []
    for _order, version, rel in newer[:CANDIDATES]:
        tag, name = f"{app}-v{version}", f"RUSE-{APPS[app]}-Setup-{version}.exe"
        listed = rel.get("assets") if isinstance(rel.get("assets"), list) else []
        assets = {str(a.get("name")): a for a in listed if isinstance(a, dict)}
        data = fetch_sig(f"{DOWNLOADS}{tag}/{name}{releasesig.SUFFIX}") if name + releasesig.SUFFIX in assets else None
        payload, _why = releasesig.read(data) if data is not None else (None, "no signature")
        if payload is None or releasesig.fits(payload, app, version, tag, name):
            ignored.append(version)
            continue
        return _offer(app, version, rel, assets, payload, current, ignored)
    raise UpdateError(f"{APPS[app]} {newer[0][1]} is out, but we can't confirm it's ours, so it isn't installed.",
                      final=True, version=newer[0][1])


def _offer(app: str, version: str, rel: dict, assets: dict, payload: dict, current: str, ignored: list) -> Release:
    tag, name = f"{app}-v{version}", f"RUSE-{APPS[app]}-Setup-{version}.exe"
    book = NOTES_ASSET.format(app=APPS[app])
    found = Release(app, version, tag, f"{RELEASES_PAGE}/tag/{tag}", name, f"{DOWNLOADS}{tag}/{name}",
                    payload["size"], payload["sha256"], [], f"{DOWNLOADS}{tag}/{book}",
                    payload["required"] if releasesig.required_for(payload, current) else "",
                    payload["notes_size"], payload["notes_sha256"], payload["key"], payload["commit"], ignored)
    asset = assets.get(name)
    if asset is None:
        found.refused = _refused(f"{APPS[app]} {version} is out, but its installer ({name}) isn't in the release yet.")
    elif not rel.get("feed"):   # the API lists each file's size, and GitHub's digest of it (the feed lists neither)
        digest = str(asset.get("digest") or "")
        if asset.get("size") != payload["size"] or (digest and digest.lower() != "sha256:" + payload["sha256"]):
            found.refused = _refused(f"{APPS[app]} {version}'s installer on GitHub isn't the one we signed (its size "
                                     f"or SHA-256 differs), so it isn't installed.")
    return found


def _refused(text: str) -> str:
    """Why a signed release's installer isn't installed, in words for people (rusemod.buildtext lists them from the
    calls to this and says them in the player's language)."""
    return text


def checked_notes(rel: Release, opener=None) -> dict | None:
    """The release's notes file ({language code: notes}) when its size and SHA-256 are the signed ones, else None."""
    if not rel.notes_url.startswith(DOWNLOADS) or not 0 < rel.notes_size <= NOTES_MAX:
        return None
    try:
        with (opener or _open)(rel.notes_url) as resp:
            data = resp.read(rel.notes_size + 1)
    except (UpdateError, OSError, ValueError, http.client.HTTPException):
        return None
    if len(data) != rel.notes_size or hashlib.sha256(data).hexdigest() != rel.notes_sha256:
        return None
    try:
        book = json.loads(data.decode("utf-8-sig"))
    except ValueError:
        return None
    return book if isinstance(book, dict) else None


def changes_in(rel: Release, lang: str, current: str, opener=None) -> list:
    """The release's changes since `current` in language `lang` (the apps' codes: fr, ger, ...), from its checked notes
    file (checked_notes): English ("us") for English, the game's own names ("base") and a language the notes haven't
    got; nothing when the file can't be had or isn't the signed one (never the release text)."""
    book = checked_notes(rel, opener)
    if book is None:
        return []
    english = changes_since(book.get("us"), current, rel.version) if isinstance(book.get("us"), str) else []
    if not lang or lang in ("us", "base"):
        return english
    text = book.get(lang)
    local = changes_since(text, current, rel.version) if isinstance(text, str) else []
    mine = {r["version"] for r in local}
    # version by version: in the language where its notes have that version, else in English (someone two versions
    # behind sees both, the older one in English when it was never translated)
    out, done = [], set()
    for r in english:
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


def _length(resp) -> int | None:
    """The size the server says it sends (Content-Length), or None when it says none."""
    try:
        value = resp.headers.get("Content-Length") if getattr(resp, "headers", None) is not None else None
        return int(value) if value is not None and str(value).strip().isdigit() else None
    except (AttributeError, TypeError, ValueError):
        return None


def download(rel: Release, folder: Path, progress=lambda done, total: None, opener=_open) -> Path:
    """Download the installer into `folder`, checking its size and SHA-256 against the signed ones as it comes.
    Returns its path. A file that isn't the signed one is refused (final) and deleted; a download that stops before the
    end is refused as not done yet (try again)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / rel.asset
    part = target.with_suffix(".part")
    h = hashlib.sha256()
    done = 0
    try:
        with opener(rel.url) as resp, part.open("wb") as f:
            length = _length(resp)
            if length is not None and length != rel.size:
                raise UpdateError("the installer on GitHub isn't the one we signed (its size differs), so it wasn't "
                                  "downloaded.", final=True)
            while True:
                chunk = resp.read(min(1 << 16, rel.size + 1 - done))
                if not chunk:
                    break
                done += len(chunk)
                if done > rel.size:
                    raise UpdateError("the downloaded installer is bigger than the one we signed, so it was deleted.",
                                      final=True)
                f.write(chunk)
                h.update(chunk)
                progress(done, rel.size)
    except UpdateError:
        part.unlink(missing_ok=True)
        raise
    except OSError as exc:
        part.unlink(missing_ok=True)
        why = plain(exc)
        raise UpdateError(f"the download stopped ({why}).", why=why) from None
    except http.client.HTTPException:   # a cut chunked reply (IncompleteRead) isn't an OSError
        part.unlink(missing_ok=True)
        raise UpdateError("the download stopped before the end; try again.") from None
    if done < rel.size:
        part.unlink(missing_ok=True)
        raise UpdateError("the download stopped before the end; try again.")
    if h.hexdigest() != rel.sha256:
        part.unlink(missing_ok=True)
        raise UpdateError("the downloaded installer isn't the one we signed (its SHA-256 differs), so it was deleted.",
                          final=True)
    os.replace(part, target)
    return target


def _quit_soon(seconds: float = 1.0) -> None:
    import threading
    import time
    threading.Thread(target=lambda: (time.sleep(seconds), os._exit(0)), daemon=True).start()


class UpdateCalls:
    """The window API's update calls, for both apps (a mixin: the API sets UPDATE_APP and UPDATE_VERSION and has
    `_home` and `_jobs`). Tests replace `_update_fetch`, `_update_fetch_text`, `_update_fetch_sig`, `_update_opener`,
    `_update_popen` and `_update_quit`; nothing switches the signature check off."""

    UPDATE_APP = ""
    UPDATE_VERSION = "0.0.0"
    _update_fetch = staticmethod(_get_json)
    _update_fetch_text = staticmethod(_get_text)
    _update_fetch_sig = staticmethod(_get_sig)
    _update_opener = staticmethod(_open)
    _update_popen = staticmethod(subprocess.Popen)
    _update_quit = staticmethod(_quit_soon)
    _update_installed = staticmethod(installed_app)
    _update_found: Release | None = None
    _update_not_ours = False   # the last check found newer releases, none confirmed as ours

    def use_required_updates(self) -> None:
        """Play and Test in game wait for a required update (each app's app.py turns it on; tests of made-up games
        don't meet it)."""
        self._starter.required = self._update_refusal

    def _update_kept(self) -> str:
        """The signed required version this app last saw, while it's newer than the running one, else ""
        (settings.json "required_signed", which only the app writes: the window can't take it off). The older
        "required_update" came from unsigned release text and isn't read."""
        kept = settings(Path(self._home)).get("required_signed")
        version = kept.get(self.UPDATE_APP, "") if isinstance(kept, dict) else ""
        return version if isinstance(version, str) and version_tuple(version) > version_tuple(self.UPDATE_VERSION) else ""

    def _update_keep(self, version: str) -> None:
        values = settings(Path(self._home))
        kept = values.get("required_signed") if isinstance(values.get("required_signed"), dict) else {}
        if kept.get(self.UPDATE_APP, "") == version:
            return
        if version:
            kept[self.UPDATE_APP] = version
        else:
            kept.pop(self.UPDATE_APP, None)
        values["required_signed"] = kept
        save_settings(Path(self._home), values)

    def _update_tries(self, rel: Release) -> dict:
        """This release's failed tries (settings.json "update_tries": {app: {version, sha256, count, final, why}}),
        or {} when they were another release's (that entry is cleared then)."""
        values = settings(Path(self._home))
        tries = values.get("update_tries") if isinstance(values.get("update_tries"), dict) else {}
        mine = tries.get(self.UPDATE_APP)
        if not isinstance(mine, dict):
            return {}
        if (mine.get("version"), mine.get("sha256")) == (rel.version, rel.sha256):
            return mine
        tries.pop(self.UPDATE_APP, None)
        values["update_tries"] = tries
        save_settings(Path(self._home), values)
        return {}

    def _update_tried(self, rel: Release, exc: Exception) -> None:
        """Keep a failed try of `rel`: how many so far, and whether it was the wrong file (final)."""
        values = settings(Path(self._home))
        tries = values.get("update_tries") if isinstance(values.get("update_tries"), dict) else {}
        mine = tries.get(self.UPDATE_APP) if isinstance(tries.get(self.UPDATE_APP), dict) else {}
        if (mine.get("version"), mine.get("sha256")) != (rel.version, rel.sha256):
            mine = {}
        count = mine.get("count") if type(mine.get("count")) is int else 0
        tries[self.UPDATE_APP] = {"version": rel.version, "sha256": rel.sha256, "count": count + 1,
                                  "final": bool(getattr(exc, "final", False)), "why": str(exc)}
        values["update_tries"] = tries
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
        """Is there a newer release of this app, confirmed as ours? {"available", "version", "current" (the running
        one), "changes" (before and after, per version since the running one, in `lang` when the release's checked
        notes have it: changes_in), "page", "size", "installed" (False when running from the repo), "error",
        "required" (it must go in: the window installs it by itself and can't be used meanwhile), "offline" (a
        required update seen before, GitHub unreachable now), "unconfirmed" (newer releases are there, none confirmed
        as ours: nothing to install; "version" stays the running one), "unconfirmed_version" (the newest such one),
        "refused" (the confirmed release's file isn't the one signed: not installed), "gave_up" and "tries" (it didn't
        download after TRIES tries: no install by itself any more), "why"}. Asked once per start, and again when the
        language changes."""
        current = self.UPDATE_VERSION
        prefs = getattr(self, "prefs", None)   # (asked without a language: the window's own)
        said_in = lang if lang not in ("", "us") or prefs is None else (prefs().get("lang") or "us")
        try:
            rel = latest(self.UPDATE_APP, current, fetch=self._update_fetch, fetch_text=self._update_fetch_text,
                         fetch_sig=self._update_fetch_sig)
        except UpdateError as exc:
            if not exc.final:
                kept = self._update_kept()
                return {"available": False, "error": words(exc, said_in), "current": current,
                        **({"required": True, "offline": True, "version": kept} if kept else {})}
            # GitHub answered: newer releases, none of them ours as signed. Nothing installs and no requirement stands
            # (none is signed); the page says so and points to our Discord. Bug Watch counts nothing for it.
            self._update_found, self._update_not_ours = None, True
            self._update_keep("")
            return {"available": False, "version": current, "current": current, "unconfirmed": True,
                    "unconfirmed_version": exc.version or "", "why": words(exc, said_in)}
        self._update_found, self._update_not_ours = rel, False
        self._update_keep(rel.required if rel is not None else "")
        if rel is None:
            return {"available": False, "version": current, "current": current}
        said = {"version": rel.version, "current": current, "page": rel.page, "size": rel.size,
                "installed": bool(self._update_installed()), "required": bool(rel.required)}
        if rel.ignored:
            said["unconfirmed_version"] = rel.ignored[0]
        tried = self._update_tries(rel)
        if rel.refused or tried.get("final"):   # signed, but the file isn't the signed one: not offered
            why = UpdateError(rel.refused) if rel.refused else UpdateError(str(tried.get("why") or ""))
            return {"available": False, "refused": True, "why": words(why, said_in), **said}
        if getattr(self, "_update_offered", None) != rel.version:  # Bug Watch: once per version offered, per run
            self._update_offered = rel.version
            from . import bugwatch
            bugwatch.count("updates", "offered")
        out = {"available": True, "changes": changes_in(rel, lang, current, opener=self._update_opener), **said}
        if type(tried.get("count")) is int and tried["count"] >= TRIES:
            out.update(gave_up=True, tries=tried["count"])
        return out

    def update_page(self) -> dict:
        """Open, in the browser, where to go for this update: our Discord when it can't be confirmed as ours (his
        words of 2026-11-25), else the confirmed release's page (what's new, and its installer to download by hand),
        else the list of releases."""
        from .owned import DISCORD
        from .play import open_url
        rel = self._update_found
        if self._update_not_ours or (rel is not None and (rel.refused or self._update_tries(rel).get("final"))):
            url = DISCORD
        elif rel is not None and rel.page.startswith(f"{RELEASES_PAGE}/tag/"):
            url = rel.page
        else:
            url = RELEASES_PAGE
        (getattr(self, "_update_open_url", None) or open_url)(url)
        return {"opened": url}

    def update_install(self) -> dict:
        """Download the newer installer, check it against the signed size and SHA-256, run it silently and quit (the
        installer starts the app again). Returns {"job": id}; the job's lines say how far the download is. Each
        failed try is kept (update_check's "refused" and "gave_up")."""
        from .webui import Job
        rel = self._update_found
        if rel is None:
            raise UpdateError("There's no update to install (look again after starting the app).")
        if not self._update_installed():
            raise UpdateError("This copy runs from the repo, not from an installer: update it with git pull.")
        if rel.refused:
            raise UpdateError(rel.refused, final=True, version=rel.version)
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
            except Exception as exc:
                bugwatch.count("updates", "failed")
                try:
                    self._update_tried(rel, exc)
                except OSError:
                    pass   # (a settings file that can't be written: the try isn't kept, the refusal still shows)
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
