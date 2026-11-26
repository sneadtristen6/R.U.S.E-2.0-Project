"""Help and bug reports, for both apps: the wiki (the field manual), Discussions, the project's GitHub issues, and a
bug report opened in the browser with the app, its version and the message filled in. Nothing is ever sent from the
apps: the player reads the report and posts it themselves on GitHub.

A message can hold paths, and paths hold the Windows user name (C:\\Users\\<name>\\...): the report shortens them to
%LOCALAPPDATA% / %USERPROFILE% first, so a public post never shows who the player is on their PC.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote, urlencode

from .mod_index import PAGE as MOD_LIST_PAGE
from .owned import TICKET as ISSUES   # the project's GitHub issues, a new one (the owned-copies ticket opens there too)

REPO_URL = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project"
LINKS = {"wiki": f"{REPO_URL}/wiki", "discussions": f"{REPO_URL}/discussions",
         "help": f"{REPO_URL}/discussions/categories/help",
         "mods": MOD_LIST_PAGE,  # the supported-mods list (MOD_FORMAT §15): see it, or add a mod to it
         "guidelines": f"{MOD_LIST_PAGE}/blob/main/GUIDELINES.md",  # what the list accepts
         # the Launcher's crash notice: "GitHub" (the owner, 2026-11-26: "send this report to me on either GitHub or
         # Discord"; ruse_launcher/ui/app.js crashParts), where the player posts the code and the screenshot
         "issues": ISSUES}
# the wiki's first page in each of the apps' languages (the owner, 2026-10-30: "a wiki for every language we
# support"; docs/wiki/<code>/, each page named by its title in that language); English is the wiki's Home
WIKI_HOMES = {"fr": "Manuel-de-terrain", "ger": "Feldhandbuch", "ita": "Manuale-da-campo", "spa": "Manual-de-campaña",
              "pol": "Podręcznik-polowy", "ru": "Полевое-руководство", "cz": "Polní-příručka",
              "jpn": "フィールドマニュアル", "sc": "野战手册", "fa": "راهنمای-میدانی"}
# the wiki's page on each of the Studio's hard boxes, in each of the apps' languages, for the "Having trouble? Read the
# guide" link beside them (ruse_studio/ui/app.js troubleLink; the owner, 2026-11-13: "maybe have like a link somewhere
# in the thing where it's like having trouble wiki ... I don't want it to look stupid"): bones (Its two halves, Will
# it work in the game?), animations (Its animations, RUSE Decoy's), blender (Open in Blender and Bring my changes back)
WIKI_TOPICS = {
    "bones": {"us": "Models-and-Bones", "fr": "Modèles-et-os", "ger": "Modelle-und-Knochen", "ita": "Modelli-e-ossa",
              "spa": "Modelos-y-huesos", "pol": "Modele-i-kości", "ru": "Модели-и-кости", "cz": "Modely-a-kosti",
              "jpn": "モデルとボーン", "sc": "模型与骨骼", "fa": "مدل‌ها-و-استخوان‌ها"},
    "animations": {"us": "Unit-Animations", "fr": "Animations-des-unités", "ger": "Animationen-der-Einheiten",
                   "ita": "Animazioni-delle-unità", "spa": "Animaciones-de-las-unidades", "pol": "Animacje-jednostek",
                   "ru": "Анимации-юнитов", "cz": "Animace-jednotek", "jpn": "ユニットのアニメーション", "sc": "单位动画",
                   "fa": "انیمیشن‌های-یگان‌ها"},
    "blender": {"us": "Open-in-Blender", "fr": "Ouvrir-dans-Blender", "ger": "In-Blender-öffnen", "ita": "Apri-in-Blender",
                "spa": "Abrir-en-Blender", "pol": "Otwórz-w-Blenderze", "ru": "Открыть-в-Blender",
                "cz": "Otevřít-v-Blenderu", "jpn": "Blenderで開く", "sc": "在-Blender-中打开", "fa": "باز-کردن-در-Blender"},
    # squad: Change a squad (a helmet, backpack or bazooka on one soldier, models or a uniform), import: Import a model
    # (a model with bones and animations of its own); the 0.9.8.22 promises 52e, 52f, 52v
    "squad": {"us": "Change-a-Squad", "fr": "Changer-une-escouade", "ger": "Einen-Trupp-ändern",
              "ita": "Cambiare-una-squadra", "spa": "Cambiar-un-pelotón", "pol": "Zmiana-oddziału",
              "ru": "Изменение-отряда", "cz": "Změna-družstva", "jpn": "分隊の変更", "sc": "修改小队",
              "fa": "تغییر-جوخه"},
    "import": {"us": "Import-a-Model", "fr": "Importer-un-modèle", "ger": "Ein-Modell-importieren",
               "ita": "Importare-un-modello", "spa": "Importar-un-modelo", "pol": "Importowanie-modelu",
               "ru": "Импорт-модели", "cz": "Import-modelu", "jpn": "モデルの取り込み", "sc": "导入模型",
               "fa": "وارد-کردن-مدل"},
}
BUG_CATEGORY = "bug-reports"      # the category's slug: .github/DISCUSSION_TEMPLATE/bug-reports.yml is its form
APP_NAMES = {"studio": "RUSE Studio", "launcher": "RUSE Launcher"}  # as the form's "Which app?" lists them
MESSAGE_MOST = 1500               # characters of a message that go into the link (a long URL gets refused)
# C:\Users\<name>, any drive, either slash, any number of them (Python prints a path's \ as \\), or from the drive's
# root (\Users\<name>, with \ only: a web address's /users/ is no folder); and a home folder as Wine shows Linux's
# (Z:\home\<name>: the game on a Steam Deck or under Proton). A name can hold spaces and ' (Nick Smith, O'Brien): it
# goes up to its next slash, else up to a closing quote, else it is one word; never past a character Windows keeps
# out of a user name (" / \ [ ] : ; | = , + * ? < >) or the line's end (2026-11-24)
_USERS = re.compile(r"(?i)(?:\b[a-z]:[\\/]+(?:users|home)|(?<![^\s\"'(\[=,;])\\+users)[\\/]+"
                    r"(?:[^\"/\\\[\]:;|=,+*?<>\r\n]+(?=[\\/])|[^\"'/\\\[\]:;|=,+*?<>\r\n]+(?=[\"'])"
                    r"|[^\s\"'/\\\[\]:;|=,+*?<>]+)")


def _written_anyhow(folder: str):
    """`folder` (as Windows names it) as a pattern that finds it in any case, written with either slash and any number
    of them: as Windows writes it, as Python prints it (each \\ doubled) or with /. None for a drive alone."""
    parts = re.split(r"[\\/]+", folder.rstrip("\\/"))
    return re.compile(r"[\\/]+".join(re.escape(p) for p in parts), re.IGNORECASE) if len(parts) > 1 else None


def _documents():
    from .yourfiles import documents
    try:
        return documents()
    except Exception:  # noqa: BLE001 - a report goes out even when Windows can't say
        return None


def private_paths_out(text: str) -> str:
    """`text` with the player's own folders written the way Windows names them for anyone: %LOCALAPPDATA%,
    %APPDATA%, %USERPROFILE%, then any other C:\\Users\\<name> left. A Documents folder moved out of the player's own
    (where the Studio keeps mods: rusemod.yourfiles) is written as Documents: its path can carry a name too. Each is
    found however it is written: either slash, and Python's doubled \\ (the game's error text prints a path so)."""
    out = str(text or "")
    docs, own = _documents(), os.environ.get("USERPROFILE") or str(Path.home())
    if docs and not str(docs).lower().startswith(own.lower().rstrip("\\/") + "\\"):
        found = _written_anyhow(str(docs))
        out = found.sub("Documents", out) if found else out
    for var in ("LOCALAPPDATA", "APPDATA", "USERPROFILE"):
        value = os.environ.get(var) or (str(Path.home()) if var == "USERPROFILE" else "")
        found = _written_anyhow(value) if value else None
        if found:
            out = found.sub(f"%{var}%", out)
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


def wiki_url(lang: str | None, topic: str | None = None) -> str:
    """The wiki's first page in `lang` (the apps' codes), the English wiki for English or any other; with `topic` (one
    of WIKI_TOPICS), that topic's page in `lang`, the English one for any other language."""
    if topic:
        pages = WIKI_TOPICS[topic]
        return f"{REPO_URL}/wiki/{quote(pages.get(lang or '') or pages['us'])}"
    home = WIKI_HOMES.get(lang or "")
    return f"{REPO_URL}/wiki/{quote(home)}" if home else LINKS["wiki"]


class CommunityCalls:
    """The window API's help calls, for both apps (a mixin beside rusemod.update.UpdateCalls, whose UPDATE_APP,
    UPDATE_VERSION and `_update_open_url` it uses, and home.PrefsCalls, whose language it opens the wiki in)."""

    def _community_lang(self) -> str | None:
        try:
            return (self.prefs() or {}).get("lang")
        except Exception:  # noqa: BLE001  (no settings yet, or unreadable: the English wiki)
            return None

    def help_links(self) -> dict:
        """The wiki's (in the player's language) and Discussions' addresses, for the window to show."""
        return dict(LINKS) | {"wiki": wiki_url(self._community_lang())}

    def open_help(self, what: str, topic: str | None = None) -> dict:
        """Open the wiki ("wiki", in the player's language; with `topic`, one of WIKI_TOPICS, that topic's page),
        Discussions ("discussions"), its Help category ("help"), the supported-mods list's page ("mods") or a new
        issue on the project's GitHub ("issues", the Launcher's crash notice) in the browser."""
        if what not in LINKS:
            raise ValueError(f"There's no help page called {what!r}")
        if topic is not None and (what != "wiki" or topic not in WIKI_TOPICS):
            raise ValueError(f"There's no wiki page called {topic!r}")
        return self._community_open(wiki_url(self._community_lang(), topic) if what == "wiki" else LINKS[what])

    def report_problem(self, message: str = "") -> dict:
        """Open a new bug report in the browser, the app, its version and `message` (an error the window showed)
        filled in. Returns {"opened": the address}."""
        return self._community_open(report_url(self.UPDATE_APP, self.UPDATE_VERSION, message))

    def _community_open(self, url: str) -> dict:
        from .play import open_url
        (getattr(self, "_update_open_url", None) or open_url)(url)
        return {"opened": url}
