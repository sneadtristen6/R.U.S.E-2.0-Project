"""What Export mod (rusemod.package.pack, the Studio's export_mod) lets out of the maker's PC, after the owner's answers
of 2026-11-12 (his question dialog, as the lead quoted them):
- the era units' credits and record go along ("Take both along"): CREDITS-era-units.md (every era unit maker's CC-BY
  credit, and "your name, sneadtristen6, in that mod's credits" for the Horse Squad) and era_units.json (which units
  are era units), so another player's Studio knows them as added: its Take it out works there, its Add says the unit
  is in the mod already. A mod without era units packs as before, byte for byte;
- no folder of the maker's PC goes out (FL-110, "Keep file name only": Export writes only the file's own name in each
  record, never a folder) in the fields the Studio itself writes a path into: a model's record ("from", the pictures
  its report names), the data inside a .glb the Studio made from a scenery model (the file it was made from), a map's
  import record (its folders); the mod's own files on his PC keep theirs. Round 2 (the export recheck's F2 and F1):
  nothing a modder wrote changes (README, description, .rndf, .csv, credits: byte for byte), the Studio's fields name
  their file on any system. A record naming only a file's name is never looked for in the folder the Studio runs in
  (Resize and Move take a model's file only by its full path).
On the Studio tests' made-up game, the Horse Squad's builder and model import stood in for (as tests/test_horse_squad.py
does): what's checked here is what goes into the file and comes out of it."""
import codecs
import json
import tomllib
import os
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_build import write_mod
from test_horse_squad import finished, stand_in
from test_studio import WithMod
from rusemod import package
from rusemod.gltf import _Glb
from rusemod.library import Library
from rusemod.modelin import glb_document
from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError

KEY = horse_squad.KEY
LIBERTY = "WWI|USA|Mark VIII Liberty"
LIBERTY_LINE = '- Mark VIII Liberty (WWI, USA): "Liberty model" by maker, CC-BY 4.0, https://example.org/Liberty.'
HIS_LINE = "- Generic Horse (WWII, USA): by sneadtristen6."
PC = "C:\\Users\\Jane Doe\\AppData\\Local\\RUSE Mod Platform"   # a player's platform folder, his Windows name in it


def era_library(folder: Path) -> Path:
    """An era units library with one WWI unit (no model) copying the M4 Sherman, as test_horse_squad's."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": [
        {"key": LIBERTY, "era": "WWI", "nation": "USA", "name": "Mark VIII Liberty",
         "in_place_of": "", "card": "Heavy Tank", "building": "Armor base",
         "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "", "game_nation": 0,
         "factory": 10, "aircraft": False, "model": None, "fits": True, "picture": None,
         "credit": {"title": "Liberty model", "author": "maker", "licence": "CC-BY 4.0",
                    "url": "https://example.org/Liberty", "extra": ""}}]}), encoding="utf-8")
    return folder


def glb_naming(source: str) -> bytes:
    """A .glb as the Studio's scenery import writes a model's version (rusemod.meshlod.glb_bytes): its mesh and its
    asset's extras name the file it was made from."""
    g = _Glb()
    g.doc["meshes"] = [{"name": source, "primitives": [{"attributes": {"POSITION": g.packed(
        struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), 3, "VEC3", 5126, low=[0, 0, 0], high=[1, 1, 0])}}]}]
    g.doc["nodes"] = [{"name": "model", "mesh": 0}]
    g.doc["scenes"] = [{"nodes": [0]}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_version": source}
    return g.to_bytes()


def members(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


# (round 2 of the export fix, 2026-11-12: "Export never changes what a modder wrote, except a folder of this PC that
# the Studio itself put there, and then only that folder." Round 1's folders_out read paths out of any text and cut a
# modder's words, the recheck's F2; it is gone, and these tests say what replaced it.)
# Every text the export recheck's probe (fix-export/recheck1/try_paths.py) tried, with the README line of its F2 test:
MODDER_TEXTS = ("/var/home/jane/Models/tank.glb", "/Volumes/Jane Drive/models/tank.glb", "/opt/models/tank.glb",
                "/data/jane/models/tank.glb", "~/Models/tank.glb", "made from `/home/jane/x.glb`",
                "file:///home/jane/x.glb", "made from (/home/jane/x.glb)", "file:///C:/Users/jane/x.glb",
                "\\\\?\\C:\\Users\\jane\\x.glb", "Plan B:/C", "Hold sector A:\\ then B", "Phase 1: Take bridge X:/Y",
                "%USERPROFILE%\\Documents\\tank.glb", "C:\\Users\\jane\\x.glb; then see the manual\\page 3",
                "Made from C:\\models\\tank.glb, and docs\\turret.md tells how.", "https://example.org/x")
# What each becomes in his README (the owner, 2026-11-13, to "A folder path in a modder's own README, in an exported
# mod: cut it to the file name, or keep it with a warning?": "cut to file name"): only a path that names a folder is
# cut, to the name after its last slash, every word around it as written; "Plan B:/C" and the like name no folder
README_CUT = {"/var/home/jane/Models/tank.glb": "tank.glb", "/Volumes/Jane Drive/models/tank.glb": "tank.glb",
              "/opt/models/tank.glb": "tank.glb", "/data/jane/models/tank.glb": "tank.glb",
              "~/Models/tank.glb": "tank.glb", "made from `/home/jane/x.glb`": "made from `x.glb`",
              "file:///home/jane/x.glb": "x.glb", "made from (/home/jane/x.glb)": "made from (x.glb)",
              "file:///C:/Users/jane/x.glb": "x.glb", "\\\\?\\C:\\Users\\jane\\x.glb": "x.glb",
              "Plan B:/C": "Plan B:/C", "Hold sector A:\\ then B": "Hold sector A:\\ then B",
              "Phase 1: Take bridge X:/Y": "Phase 1: Take bridge X:/Y",
              "%USERPROFILE%\\Documents\\tank.glb": "tank.glb",
              "C:\\Users\\jane\\x.glb; then see the manual\\page 3": "x.glb; then see the manual\\page 3",
              "Made from C:\\models\\tank.glb, and docs\\turret.md tells how.":
                  "Made from tank.glb, and docs\\turret.md tells how.",
              "https://example.org/x": "https://example.org/x"}


class StudioPaths(unittest.TestCase):
    def test_a_path_the_studio_wrote_keeps_its_file_s_own_name_on_any_system(self):
        for text, want in (
                (PC + "\\horse_squad\\horse-squad-rifle.glb", "horse-squad-rifle.glb"),
                ("D:/RUSE-2.0/scratch/x/Boulder01.glb (far)", "Boulder01.glb (far)"),
                ("\\\\server\\share\\models\\tank.glb", "tank.glb"),
                ("/home/jane/models/tank.glb", "tank.glb"),
                ("/var/home/jane/.local/share/ruse-mod-platform/horse_squad/horse-squad-rifle.glb",
                 "horse-squad-rifle.glb"),
                ("/Volumes/Jane Drive/models/tank.glb", "tank.glb"), ("/opt/models/tank.glb", "tank.glb"),
                ("/data/jane/models/tank.glb", "tank.glb"), ("~/Models/tank.glb", "tank.glb"),
                ("file:///home/jane/x.glb", "x.glb"), ("file:///C:/Users/jane/x.glb", "x.glb"),
                ("\\\\?\\C:\\Users\\jane\\x.glb", "x.glb"), ("%USERPROFILE%\\Documents\\tank.glb", "tank.glb"),
                ("C:\\Users\\jane\\u1945.glb", "u1945.glb"), ("C:\\Users\\Jane Doe\\Desktop\\", "Desktop"),
                ("C:\\Users\\jane\\tank (2).glb (far)", "tank (2).glb (far)"), ("tank.glb", "tank.glb")):
            self.assertEqual(package.own_name(text), want, text)

    def test_which_picture_names_are_paths(self):
        for text in (PC + "\\coat.png", "/var/home/jane/coat.png", "\\\\server\\coat.png", "~/coat.png",
                     "file:///home/jane/coat.png", "%USERPROFILE%\\coat.png", "c:/coat.png"):
            self.assertTrue(package.is_absolute(text), text)
        for text in ("coat.png", "textures/coat.png", "textures\\coat.png", "$/GFX/Everything/X",
                     "https://example.org/coat.png", "Plan B:/C", None):
            self.assertFalse(package.is_absolute(text), text)


class HisReadme(unittest.TestCase):
    """package.paths_cut, what Export does to his README (the owner, 2026-11-13: "cut to file name"): each path that
    names a folder of a disk or a home loses its folders, the name after the last slash and every word around it stay.
    Each answer is written out here by hand, never worked out by the code under test."""

    def test_a_folder_path_is_cut_to_its_name_and_no_word_goes_with_it(self):
        for text, want in (
                ("Made from C:\\models\\tank.glb and docs\\turret.md", "Made from tank.glb and docs\\turret.md"),
                ("Made on C:\\Users\\Jane Doe\\AppData\\Local\\RUSE Mod Platform\\mods\\cavalry by me.",
                 "Made on cavalry by me."),
                ("I keep them in /home/jane/mods and /home/jane/maps.", "I keep them in mods and maps."),
                ("Put it in C:\\Mods\\MyMod\\ and play", "Put it in MyMod\\ and play"),
                ("C:\\Program Files (x86)\\Steam\\steamapps\\common\\R.U.S.E\\ZZ_Win.dat", "ZZ_Win.dat"),
                ("[my model](C:\\Users\\jane\\tank.glb)", "[my model](tank.glb)"),
                ("see /home/jane/x.glb and/or /tmp", "see x.glb and/or /tmp"),
                ("\\\\server\\share\\models\\tank.glb", "tank.glb"),
                ("E:\\Mods & Models\\Jane's (2026)\\horse-squad-rifle.glb", "horse-squad-rifle.glb"),
                ("C:\\Users\\jane\\My Tank.glb is mine", "My Tank.glb is mine"),
                ("C:/Users/jane/x.glb", "x.glb"), ("path=C:\\Users\\jane\\x.glb", "path=x.glb"),
                ("D:\\RUSE-2.0\\scratch\\x\\Boulder01.glb (far)", "Boulder01.glb (far)"),
                ("C:\\Mods\\Version 2.0 Final\\tank.glb", "tank.glb"),
                ("C:\\\\Users\\\\jane\\\\x.glb", "x.glb"), ("two: C:\\a\\b.glb, D:\\c\\d.glb.", "two: b.glb, d.glb."),
                ("Made from C:\\models\\tank.glb, and docs\\turret.md tells how.",
                 "Made from tank.glb, and docs\\turret.md tells how."),
                ("*~/Models/tank.glb*", "*tank.glb*"), ("%APPDATA%\\x\\y.glb", "y.glb"),
                # (from READMEs of the tools on this PC, 2026-11-13: words between two paths, a switch, an escape)
                ("in /usr/tmp/python (assuming ~guido/src/python is the toplevel",
                 "in python (assuming ~guido/src/python is the toplevel"),
                ("cl /Iinclude share\\doc\\gmsh\\t1.cpp lib\\gmsh.lib", None),
                ("cssesc gives 'Ich \\\\2665  B\\\\FC cher'", None)):
            self.assertEqual(package.paths_cut(text)[0], text if want is None else want, text)

    def test_what_names_no_folder_stays(self):
        for text in ("Join /r/ruse today", "C:\\tank.glb", "a\\b\\c and docs/x.md", "Plan B:/C",
                     "Hold sector A:\\ then B", "Phase 1: Take bridge X:/Y", "https://example.org/a/b/c.glb",
                     "By sneadtristen6: https://github.com/sneadtristen6/R.U.S.E-2.0-Project", "1/2/3", "and/or",
                     "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger", "~/x.glb", "/opt/x.glb", ""):
            self.assertEqual(package.paths_cut(text), (text, []), text)

    def test_what_export_says_of_each_cut(self):
        self.assertEqual(package.paths_cut("Made from C:\\models\\tank.glb, and more")[1],
                         [("C:\\models\\tank.glb,", "tank.glb,")])
        self.assertEqual(package.cut_shown("C:\\models\\tank.glb,", "tank.glb,"), "C:\\models\\tank.glb \u2192 tank.glb")
        self.assertEqual(package.cut_shown("C:\\a\\x.glb)", "x.glb)"), "C:\\a\\x.glb \u2192 x.glb")
        self.assertEqual(package.cut_shown("C:\\a\\tank (2).glb", "tank (2).glb"), "C:\\a\\tank (2).glb \u2192 tank (2).glb")

    def test_a_path_that_ends_at_a_user_s_own_folder_goes_whole(self):
        """The owner, 2026-11-13, to "A path that ends at the user folder, such as "C:\\Users\\Jane Doe", keeps the
        user name. Take those paths out completely?": "Probably take the username path out". On e9a092c3 each of these
        kept the user's name ("Made on Jane Doe by me."). Each answer is written out here by hand."""
        for text, want, gone in (
                ("Made on C:\\Users\\Jane Doe by me.", "Made on  by me.", "C:\\Users\\Jane Doe"),
                ("Made on C:\\Users\\Jane Doe.", "Made on .", "C:\\Users\\Jane Doe"),
                ("Made on C:\\Users\\jane, then more", "Made on , then more", "C:\\Users\\jane"),
                ("D:/Users/Jane Q Doe is mine", " is mine", "D:/Users/Jane Q Doe"),
                ("c:\\users\\JANE DOE and Bob", " and Bob", "c:\\users\\JANE DOE"),
                ("C:\\Users\\Jane Doe\\ and more", " and more", "C:\\Users\\Jane Doe\\"),     # (its slash after it)
                ('Set "C:\\Users\\jane doe" there', 'Set "" there', "C:\\Users\\jane doe"),    # (in quotes: to them)
                ("[home](C:\\Users\\Jane Doe)", "[home]()", "C:\\Users\\Jane Doe"),
                ("`C:\\Users\\jane doe`", "``", "C:\\Users\\jane doe"),
                ("(see C:\\Users\\Jane Doe)", "(see )", "C:\\Users\\Jane Doe"),
                ("\\\\server\\Users\\jane is shared", " is shared", "\\\\server\\Users\\jane"),   # a server's share
                ("\\\\?\\C:\\Users\\Jane Doe", "", "\\\\?\\C:\\Users\\Jane Doe"),
                ("file:///C:/Users/Jane%20Doe", "", "file:///C:/Users/Jane%20Doe"),
                ("C:\\\\Users\\\\jane", "", "C:\\\\Users\\\\jane"),
                ("C:\\Documents and Settings\\Jane Doe", "", "C:\\Documents and Settings\\Jane Doe"),
                ("/var/home/jane", "", "/var/home/jane"), ("see /home/jane", "see ", "/home/jane"),
                ("/usr/home/jane", "", "/usr/home/jane"), ("file:///home/jane", "", "file:///home/jane"),
                ("file://server/Users/jane", "", "file://server/Users/jane"),
                ("%SystemDrive%\\Users\\jane", "", "%SystemDrive%\\Users\\jane"),
                ("D:\\Users\\Mary Ann Smith-Jones and more", " and more", "D:\\Users\\Mary Ann Smith-Jones"),
                ("C:\\Users\\Jane!", "!", "C:\\Users\\Jane"),
                ("C:\\Users\\jsmith.CONTOSO is mine", " is mine", "C:\\Users\\jsmith.CONTOSO"),
                ("C:\\Users\\Иван Петров\nnext line", "\nnext line", "C:\\Users\\Иван Петров")):
            self.assertEqual(package.paths_cut(text), (want, [(gone, "")]), text)
        self.assertEqual(package.paths_cut("/home/jane and /Users/jane"), (" and ", [("/home/jane", ""),
                                                                                   ("/Users/jane", "")]))

    def test_a_user_s_name_known_exactly_goes_whole(self):
        """A user's name in small letters with a space: known from this PC's own home folder (pack's), or from the same
        text writing it with a slash after it; else only its first word is sure to be the name. Where such a name ends
        when it isn't known (C:\\Users\\kim lee by me: "lee" or "lee by"?) is a question for the owner (the export
        fix's report): this test says only what is sure, the first word gone."""
        text = "Made on C:\\Users\\kim lee by me"
        self.assertEqual(package.paths_cut(text, ("kim lee",)), ("Made on  by me", [("C:\\Users\\kim lee", "")]))
        new, cuts = package.paths_cut(text)
        self.assertNotIn("kim", new)
        self.assertEqual((new[:len("Made on ")], cuts[0][0][:len("C:\\Users\\kim")], cuts[0][1]),
                         ("Made on ", "C:\\Users\\kim", ""))
        self.assertEqual(package.paths_cut("C:\\Users\\kim lee\\x.glb and C:\\Users\\kim lee too"),
                         ("x.glb and  too", [("C:\\Users\\kim lee\\x.glb", "x.glb"), ("C:\\Users\\kim lee", "")]))
        self.assertEqual(package.user_of("C:\\Users\\kim lee\\AppData\\Local\\RUSE Mod Platform"), "kim lee")
        self.assertEqual(package.user_of("/home/kim"), "kim")
        self.assertIsNone(package.user_of("D:\\Games\\RUSE"))

    def test_every_way_a_path_is_written_to_a_user_s_own_folder_goes_whole(self):
        """The export fix's review (2026-11-13), defects 1 and 2: Git Bash's, WSL's and Cygwin's ways to write a Windows
        drive, a drive's own share, \\\\?\\UNC\\ and file://localhost/ kept the user's name (on 1b9853b5 and on
        e9a092c3: "Built in jane with Git Bash."). As a class: the top of a Windows drive however a path writes it, a
        server's share of its users' folders, and the top of a Linux or Mac disk, each in every form. Each answer is
        written out here by hand."""
        for text, want, gone in (
                ("Built in /c/Users/jane with Git Bash.", "Built in  with Git Bash.", ["/c/Users/jane"]),
                ("Built in /C/Users/Jane Doe/ then", "Built in  then", ["/C/Users/Jane Doe/"]),
                ("WSL: /mnt/c/Users/jane is mine", "WSL:  is mine", ["/mnt/c/Users/jane"]),
                ("Cygwin: /cygdrive/d/users/jane", "Cygwin: ", ["/cygdrive/d/users/jane"]),
                ("Old: /c/Documents and Settings/jane here", "Old:  here", ["/c/Documents and Settings/jane"]),
                ("Shared from \\\\MYPC\\C$\\Users\\jane today.", "Shared from  today.", ["\\\\MYPC\\C$\\Users\\jane"]),
                ("From \\\\localhost\\d$\\Users\\jane", "From ", ["\\\\localhost\\d$\\Users\\jane"]),
                ("Share: \\\\?\\UNC\\server\\Users\\jane", "Share: ", ["\\\\?\\UNC\\server\\Users\\jane"]),
                ("Share: \\\\?\\UNC\\server\\C$\\Users\\jane", "Share: ", ["\\\\?\\UNC\\server\\C$\\Users\\jane"]),
                ("Device: \\\\.\\C:\\Users\\jane here", "Device:  here", ["\\\\.\\C:\\Users\\jane"]),
                ("Device: \\\\.\\UNC\\server\\Users\\jane", "Device: ", ["\\\\.\\UNC\\server\\Users\\jane"]),
                ("V: \\\\?\\Volume{b75e2c83-0000-0000-0000-602f00000000}\\Users\\jane", "V: ",
                 ["\\\\?\\Volume{b75e2c83-0000-0000-0000-602f00000000}\\Users\\jane"]),
                ("Set file://localhost/C:/Users/jane there", "Set  there", ["file://localhost/C:/Users/jane"]),
                ("Set file:///C|/Users/jane there", "Set  there", ["file:///C|/Users/jane"]),
                ("Set file://localhost/home/jane there", "Set  there", ["file://localhost/home/jane"]),
                ("Set file://server/C$/Users/jane there", "Set  there", ["file://server/C$/Users/jane"]),
                ("Hidden: \\\\server\\Users$\\jane and \\\\server\\home$\\kim", "Hidden:  and ",
                 ["\\\\server\\Users$\\jane", "\\\\server\\home$\\kim"]),
                ("NAS: \\\\nas\\homes\\jane today", "NAS:  today", ["\\\\nas\\homes\\jane"]),
                ("\\\\wsl$\\Ubuntu\\home\\jane and \\\\wsl.localhost\\Debian\\home\\kim", " and ",
                 ["\\\\wsl$\\Ubuntu\\home\\jane", "\\\\wsl.localhost\\Debian\\home\\kim"]),
                ("Wine: ~/.wine/drive_c/users/jane and /home/kim/.wine/drive_c/users/kim", "Wine:  and ",
                 ["~/.wine/drive_c/users/jane", "/home/kim/.wine/drive_c/users/kim"]),
                ("Mac: /Volumes/Macintosh HD/Users/jane and /System/Volumes/Data/Users/kim", "Mac:  and ",
                 ["/Volumes/Macintosh HD/Users/jane", "/System/Volumes/Data/Users/kim"]),
                ("%HomeDrive%\\Users\\jane, then %SYSTEMDRIVE%\\Users\\kim", ", then ",
                 ["%HomeDrive%\\Users\\jane", "%SYSTEMDRIVE%\\Users\\kim"]),
                ("<code>/home/jane</code> and <code>C:\\Users\\kim lee</code>", "<code></code> and <code></code>",
                 ["/home/jane", "C:\\Users\\kim lee"]),
                ("\u201c/home/jane\u201d is mine", "\u201c\u201d is mine", ["/home/jane"]),
                ("cd \\Users\\jane then", "cd  then", ["\\Users\\jane"]),           # (the drive Windows is on)
                ("C:\\Users\\JANEDO~1 is short", " is short", ["C:\\Users\\JANEDO~1"])):
            self.assertEqual(package.paths_cut(text), (want, [(g, "") for g in gone]), text)

    def test_this_pc_s_user_is_known_exactly_in_every_way_it_is_written(self):
        """This PC's own user's name (pack's, from its home folder) goes whole in each of those ways too; on 1b9853b5
        "/c/Users/kim lee made it" went out as "kim lee made it" though the name was known."""
        for text, gone in (("/c/Users/kim lee made it", "/c/Users/kim lee"),
                           ("\\\\MYPC\\C$\\Users\\kim lee made it", "\\\\MYPC\\C$\\Users\\kim lee"),
                           ("/mnt/c/Users/kim lee made it", "/mnt/c/Users/kim lee"),
                           ("file://localhost/C:/Users/kim lee made it", "file://localhost/C:/Users/kim lee")):
            self.assertEqual(package.paths_cut(text, ("kim lee",)), (" made it", [(gone, "")]), text)

    def test_a_name_in_any_language_s_quotes_or_with_a_name_s_small_words_goes_whole(self):
        """The review's defect 3, the part that is no guess: the quotes and brackets other languages write close a
        name as straight ones do (“...”, „...“, «...», 「...」); a name's own small words between its words with a
        capital go with them (Jan de Vries); a name the same text writes in quotes is known exactly. On 1b9853b5 each
        kept part of the name (" de Vries made it", "“ doe” is mine")."""
        for text, want, gone in (
                ("C:\\Users\\Jan de Vries made it", " made it", ["C:\\Users\\Jan de Vries"]),
                ("C:\\Users\\Ludwig van Beethoven", "", ["C:\\Users\\Ludwig van Beethoven"]),
                ("C:\\Users\\Maria da Silva did", " did", ["C:\\Users\\Maria da Silva"]),
                ("C:\\Users\\Juan de la Cruz did", " did", ["C:\\Users\\Juan de la Cruz"]),
                ("C:\\Users\\Jane de", " de", ["C:\\Users\\Jane"]),            # (no word with a capital after it)
                ("\u201cC:\\Users\\jane doe\u201d is mine", "\u201c\u201d is mine", ["C:\\Users\\jane doe"]),
                ("\u00abC:\\Users\\Jean Dupont\u00bb est \u00e0 moi", "\u00ab\u00bb est \u00e0 moi",
                 ["C:\\Users\\Jean Dupont"]),
                ("\u201eC:\\Users\\hans peter\u201c ist meins", "\u201e\u201c ist meins", ["C:\\Users\\hans peter"]),
                ("\u300cC:\\Users\\\u5c71\u7530 \u592a\u90ce\u300d\u306b\u3042\u308b", "\u300c\u300d\u306b\u3042\u308b",
                 ["C:\\Users\\\u5c71\u7530 \u592a\u90ce"]),
                ('Quoted once "C:\\Users\\kim lee" and then C:\\Users\\kim lee again', 'Quoted once "" and then  again',
                 ["C:\\Users\\kim lee", "C:\\Users\\kim lee"])):
            self.assertEqual(package.paths_cut(text), (want, [(g, "") for g in gone]), text)

    def test_a_path_that_names_no_user_keeps_what_it_had_before(self):
        """The review's defect 4: 1b9853b5 took out whole paths that name no user (D:\\Home\\Mods, C:\\Users\\Public,
        GET /users/me), beyond the owner's answer. Each of these keeps what e9a092c3 made of it, written out here by
        hand: Home at the top of a Windows drive, a %NAME% that isn't a drive, the system's own folders where users'
        folders are (Windows' Public, Default, All Users, desktop.ini; a Mac's Shared), a variable in a name's place,
        Users written in small letters on a Linux or Mac path, and the forms only a user's folder is looked for in."""
        for text, want in (
                ("Copy the folder to D:\\Home\\Mods and start.", "Copy the folder to Mods and start."),
                ("Put it in E:\\home\\Projects then build.", "Put it in Projects then build."),
                ("Shared files go in C:\\Users\\Public on every PC.", "Shared files go in Public on every PC."),
                ("Files in C:\\Users\\desktop.ini are hidden", "Files in desktop.ini are hidden"),
                ("New users start from C:\\Users\\Default here", "New users start from Default here"),
                ("Old ones in C:\\Users\\All Users go", "Old ones in All Users go"),
                ("And C:\\Users\\Default User too", "And Default User too"),
                ("Your folder is C:\\Users\\%USERNAME% there", "Your folder is %USERNAME% there"),
                ("Or C:\\Users\\{user} in a template", "Or {user} in a template"),
                ("%APPDATA%\\Users\\list.txt and %APPDATA%\\home\\x", "list.txt and x"),
                ("/c/Program Files/RUSE/x.exe", "x.exe"), ("/mnt/data/models/tank.glb", "tank.glb"),
                ("/c/home/x", "x"), ("file://localhost/C:/models/tank.glb", "C:/models/tank.glb"),
                ("\\\\.\\C:\\models\\tank.glb", "C:\\models\\tank.glb")):
            self.assertEqual(package.paths_cut(text)[0], want, text)
        for text in ("Linux: /home/$USER or /home/${USER}", "Mac: /Users/Shared on every Mac",
                     "GET /users/me returns your profile.", "\u201c/opt/models/tank.glb\u201d stays",
                     "<code>/opt/models/tank.glb</code> stays", "\u00ab/var/models/x.glb\u00bb",
                     "Markdown \\*stars\\* stay", "\\Windows\\System32\\x.dll", "see \\Users\\Public\\x.glb"):
            self.assertEqual(package.paths_cut(text), (text, []), text)

    def test_a_path_on_past_a_user_s_folder_loses_the_name_however_it_is_written(self):
        """A path that goes on past a user's own folder is cut to its own name, the user's name going with its folders,
        in the ways written above too: on 1b9853b5 and e9a092c3 "file://localhost/C:/Users/jane/x.glb" went out as
        "C:/Users/jane/x.glb", and \u201c/home/jane/mods/tank.glb\u201d as it was."""
        for text, want in (("file://localhost/C:/Users/jane/x.glb", "x.glb"),
                           ("\\\\.\\C:\\Users\\jane\\Desktop\\x.glb", "x.glb"),
                           ("\u201c/home/jane/mods/tank.glb\u201d", "\u201ctank.glb\u201d"),
                           ("\u00ab/Users/jane/x.glb\u00bb", "\u00abx.glb\u00bb"),
                           ("<code>/home/jane/mods/</code>", "<code>mods/</code>"),
                           ("see \\Users\\jane\\x.glb", "see x.glb"),
                           ("Built in /c/Users/jane/mods/cavalry, then", "Built in cavalry, then")):
            new, _cuts = package.paths_cut(text)
            self.assertEqual(new, want, text)
            self.assertNotIn("jane", new, text)

    def test_a_path_past_a_user_s_folder_and_what_names_no_user_stay_as_before(self):
        """The legitimate cases that must keep working: a path that goes on past the user's folder is cut to its own
        name (the user's name was one of its folders); a folder called users or home that isn't where a system keeps
        its users' folders is any folder, its file's name kept ("cut to file name"); what names no folder stays."""
        for text, want in (("C:\\Users\\Jane Doe\\Desktop\\tank.glb", "tank.glb"), ("/home/jane/mods", "mods"),
                           ("Made on C:\\Users\\Jane Doe\\AppData\\Local\\RUSE Mod Platform\\mods\\cavalry by me.",
                            "Made on cavalry by me."),
                           ("D:\\Mods\\users\\list.txt", "list.txt"), ("C:\\Mods\\home\\tank.glb", "tank.glb"),
                           ("C:\\Mods\\home\\ and", "home\\ and"), ("~/home/x.glb", "x.glb")):
            self.assertEqual(package.paths_cut(text)[0], want, text)
        for text in ("C:\\Users", "C:\\Users\\ is where", "/home", "the /home/ folder", "Join /r/ruse today",
                     "/opt/x.glb", "and/or", "~/x.glb"):
            self.assertEqual(package.paths_cut(text), (text, []), text)

    def test_which_files_are_his_readmes(self):
        for name in ("README.md", "readme.txt", "files/docs/README", "src/README-fr.md", "maps/X/Readme_old.TXT",
                     "README.en.md", "readme"):
            self.assertTrue(package.is_readme(name), name)
        for name in ("CHANGELOG.md", "LICENSE", "files/notes/readme.png", "files/readmefirst.md", "src/units.rndf",
                     "README.glb", "notreadme.md", "text/units.csv"):
            self.assertFalse(package.is_readme(name), name)


class Packing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "cavalry", {"units.rndf": "patch $/B ( ProductionPrice *= 0.5 )"},
                             extra='name = "Cavalry"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, data):
        """A file of the mod: bytes as they are, a text as the Studio writes one (its lines as the PC ends them)."""
        path = self.mod / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        (path.write_bytes if isinstance(data, bytes) else lambda t: path.write_text(t, encoding="utf-8"))(data)
        return path

    def text(self, rel) -> bytes:
        """A text as `write` wrote it, for comparing with what a package holds."""
        return self.mod.joinpath(rel).read_bytes()

    def as_before(self, out: Path) -> bytes:
        """The package a mod's files make zipped as they are, one by one (what pack wrote before it took folders out:
        z.write of each file package.files_of lists)."""
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in package.files_of(self.mod):
                z.write(f, f.relative_to(self.mod).as_posix())
        return out.read_bytes()

    def test_a_mod_without_era_units_or_folders_packs_as_before_byte_for_byte(self):
        self.write("text/units.csv", "key,us\nk1,Text\n")
        self.write("README.md", "# Cavalry\nBy sneadtristen6: https://github.com/sneadtristen6/R.U.S.E-2.0-Project\n")
        self.write("files/models/Descriptor_Unit_X.glb", glb_naming("x"))
        self.write("files/models/Descriptor_Unit_X.json", json.dumps({"from": "x.glb", "size": 1.0}, indent=1))
        self.write(era_units.INDEX, "{}")                  # (its last era unit taken out: the Studio leaves {})
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(cleaned, [])
        self.assertEqual(list(members(out)), ["mod.toml", "README.md", "src/units.rndf", "text/units.csv",
                                              "files/models/Descriptor_Unit_X.glb",
                                              "files/models/Descriptor_Unit_X.json"])   # (the {} record stays behind)
        self.assertEqual(out.read_bytes(), self.as_before(self.root / "before.zip"))

    def test_the_era_units_credits_and_record_go_along(self):
        self.write(era_units.CREDITS, f"# Made for RUSE 2.0\n\n{LIBERTY_LINE}\n{HIS_LINE}\n")
        record = {KEY: "$/GFX/Everything/Descriptor_Unit_Horse_Squad",
                  LIBERTY: "$/GFX/Everything/Descriptor_Unit_Mark_VIII_Liberty"}
        self.write(era_units.INDEX, json.dumps(record, indent=1))
        self.assertEqual([f.relative_to(self.mod).as_posix() for f in package.files_of(self.mod)],
                         ["mod.toml", era_units.CREDITS, era_units.INDEX, "src/units.rndf"])
        self.assertEqual((package.ERA_CREDITS, package.ERA_RECORD), (era_units.CREDITS, era_units.INDEX))
        out = package.pack(self.mod, self.root / "out")
        got = members(out)
        self.assertEqual(json.loads(got[era_units.INDEX]), record)
        self.assertIn(HIS_LINE.encode(), got[era_units.CREDITS])
        self.assertIn(LIBERTY_LINE.encode(), got[era_units.CREDITS])
        into = self.root / "library" / "cavalry"
        package.unpack(out, into)
        self.assertEqual((into / era_units.INDEX).read_bytes(), (self.mod / era_units.INDEX).read_bytes())
        self.assertEqual((into / era_units.CREDITS).read_bytes(), (self.mod / era_units.CREDITS).read_bytes())

    def test_a_model_record_goes_out_naming_only_its_file(self):
        coat = f"{PC}\\pictures\\coat.png"                   # (a picture the model file names, not found)
        note = f"{coat}: its alpha picture is 4 x 4, the colour 8 x 8; plain alpha used"
        mine = {"from": PC + "\\horse_squad\\horse-squad-rifle.glb", "size": 1.0, "aircraft": False,
                "report": {"file": "horse-squad-rifle.glb", "missing": [coat, "textures/belt.png"],
                           "pictures": [[coat, 4, 4]], "alpha": {coat: "plain 255"},
                           "notes": [note, "Plan B:/C and docs\\turret.md stay as written"]},
                "for": "fusilier", "skeleton": "own", "copy_kept": f"# kept\nfrom = '{coat}'\n"}
        record = self.write("files/models/Descriptor_Unit_Horse_Squad.json", json.dumps(mine, indent=1))
        on_disk = record.read_bytes()
        cleaned, kinds = [], {}
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds)
        self.assertEqual(cleaned, ["files/models/Descriptor_Unit_Horse_Squad.json"])
        self.assertEqual(kinds, {"files/models/Descriptor_Unit_Horse_Squad.json": "record"})
        self.assertEqual(record.read_bytes(), on_disk)       # his own record keeps its folder: Resize uses it
        packed = members(out)["files/models/Descriptor_Unit_Horse_Squad.json"]
        self.assertEqual(json.loads(packed), dict(mine, **{"from": "horse-squad-rifle.glb", "report": {
            "file": "horse-squad-rifle.glb", "missing": ["coat.png", "textures/belt.png"],
            "pictures": [["coat.png", 4, 4]], "alpha": {"coat.png": "plain 255"},
            "notes": [note.replace(coat, "coat.png"), "Plan B:/C and docs\\turret.md stay as written"]}}))
        # every other byte as it was: only the strings naming those paths are written anew (the uniform's text kept
        # for Take it out, copy_kept, as it was)
        self.assertEqual(packed, on_disk.replace(json.dumps(mine["from"]).encode(), b'"horse-squad-rifle.glb"')
                         .replace(json.dumps(note).encode(), json.dumps(note.replace(coat, "coat.png")).encode())
                         .replace(json.dumps(coat).encode(), b'"coat.png"'))
        self.assertEqual(json.loads(packed)["copy_kept"], mine["copy_kept"])
        with zipfile.ZipFile(self.root / "as-it-is.zip", "w", zipfile.ZIP_DEFLATED) as z:
            z.write(record, "files/models/Descriptor_Unit_Horse_Squad.json")   # (how every other member goes in)
        with zipfile.ZipFile(out) as z, zipfile.ZipFile(self.root / "as-it-is.zip") as plain:
            info, want = (zf.getinfo("files/models/Descriptor_Unit_Horse_Squad.json") for zf in (z, plain))
        self.assertEqual((info.date_time, info.external_attr, info.compress_type),
                         (want.date_time, want.external_attr, want.compress_type))   # the file's date, as z.write
        self.assertEqual(package.check(out)["files"][-1], "files/models/Descriptor_Unit_Horse_Squad.json")

    def test_a_model_s_own_data_goes_out_naming_only_its_file(self):
        model = self.write("files/assets/Boulder01/Boulder01_far.glb",
                           glb_naming(PC + "\\maps\\my-map\\files\\assets\\Boulder01\\Boulder01.glb (far)"))
        plain = self.write("files/assets/Boulder01/Boulder01.glb", glb_naming("Boulder01.glb"))
        out = package.pack(self.mod, self.root / "out")
        got = members(out)
        self.assertEqual(got["files/assets/Boulder01/Boulder01.glb"], plain.read_bytes())
        doc, binary = glb_document(got["files/assets/Boulder01/Boulder01_far.glb"])
        was, was_binary = glb_document(model.read_bytes())
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]),
                         ("Boulder01.glb (far)", "Boulder01.glb (far)"))
        self.assertEqual(binary, was_binary)
        self.assertEqual({k: v for k, v in doc.items() if k not in ("meshes", "asset")},
                         {k: v for k, v in was.items() if k not in ("meshes", "asset")})
        raw = got["files/assets/Boulder01/Boulder01_far.glb"]
        self.assertEqual(struct.unpack_from("<I", raw, 8)[0], len(raw))

    def test_only_what_the_studio_wrote_and_his_readme_s_folders_change_his_other_words_go_out_as_written(self):
        """The Studio's record and scenery model name only their files; his README goes out with the folder path in it
        cut to its own name (the owner, 2026-11-13: "cut to file name"), every other byte as he wrote it; his other
        texts (a TOML of his, a .rndf, a .csv) go out byte for byte, even naming a folder of his PC ("yes only warn"),
        and pack says which name his home folder. (Round 1 cut paths out of every text, and with them his words: the
        export recheck's F2.)"""
        self.write("files/models/Descriptor_Unit_X.json", json.dumps({"from": "D:/models/x.glb"}))
        doubled = PC.replace("\\", "\\\\")                   # (a TOML string writes each backslash twice)
        self.write("files/notes/made.toml", f'# made from {PC}\\x.blend\n[x]\nfile = "{doubled}\\\\x.glb"\n')
        self.write("README.md", f"Made on {PC}\\mods\\cavalry by sneadtristen6.\n")
        self.write("src/units.rndf", f"// made from {PC}\\x.blend; Plan B:/C\npatch $/B ( ProductionPrice *= 0.5 )\n")
        self.write("text/units.csv", f"key,us\nk1,Made from C:\\models\\tank.glb and docs\\turret.md\n")
        self.write("files/assets/A/A.glb", glb_naming("/home/jane/models/a.gltf"))
        cleaned, kinds, home_in, cuts = [], {}, [], {}
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds, home_in=home_in, home=PC,
                           cuts=cuts)
        self.assertEqual(kinds, {"files/assets/A/A.glb": "model", "files/models/Descriptor_Unit_X.json": "record",
                                 "README.md": "readme"})
        self.assertEqual(sorted(cleaned), ["README.md", "files/assets/A/A.glb", "files/models/Descriptor_Unit_X.json"])
        self.assertEqual(sorted(home_in), ["files/notes/made.toml", "src/units.rndf"])
        self.assertEqual(cuts, {"README.md": [(f"{PC}\\mods\\cavalry", "cavalry")]})
        got = members(out)
        self.assertEqual(got["README.md"], self.text("README.md").replace(f"{PC}\\mods\\".encode(), b""))
        self.assertEqual(got["README.md"].replace(b"\r\n", b"\n"), b"Made on cavalry by sneadtristen6.\n")
        self.assertIn(f"{PC}\\mods\\cavalry".encode(), self.text("README.md"))   # (his own README as he wrote it)
        for rel in ("files/notes/made.toml", "src/units.rndf", "text/units.csv", "mod.toml"):
            self.assertEqual(got[rel], self.text(rel), rel)
        self.assertEqual(json.loads(got["files/models/Descriptor_Unit_X.json"]), {"from": "x.glb"})
        doc, _binary = glb_document(got["files/assets/A/A.glb"])
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]), ("a.gltf", "a.gltf"))
        self.assertEqual(package.check(out)["id"], "cavalry")

    def test_every_text_the_recheck_tried_goes_out_as_written_but_his_readme_s_folder_paths(self):
        """Each text of the recheck's probe, in each kind of text a modder writes (mod.toml's description, a .rndf
        comment, a .csv text, CHANGELOG.md, the era credits): the member is the file, byte for byte (the owner,
        2026-11-13, "yes only warn"). In his README each folder path is cut to its own name and nothing else changes
        ("cut to file name"): README_CUT says what each text becomes, written out here, not worked out by the code."""
        texts = "\n".join(MODDER_TEXTS)
        self.write("README.md", texts + "\n")
        self.write("CHANGELOG.md", texts.encode("utf-8").replace(b"\n", b"\r\n"))
        self.write(era_units.CREDITS, f"# credits\n\n{texts}\n")
        self.write("src/units.rndf",
                   "".join(f"// {t}\n" for t in MODDER_TEXTS) + "patch $/B ( ProductionPrice *= 0.5 )\n")
        self.write("text/units.csv", "key,us\n" + "".join(f'k{i},"{t}"\n' for i, t in enumerate(MODDER_TEXTS)))
        manifest = self.mod / "mod.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8") + "description = "
                            + json.dumps(" / ".join(MODDER_TEXTS)) + "\n", encoding="utf-8")
        self.assertIn("Plan B:/C", tomllib.loads(manifest.read_text(encoding="utf-8"))["mod"]["description"])
        cleaned = []
        out = package.pack(self.mod, self.root / "out", cleaned=cleaned)
        self.assertEqual(cleaned, ["README.md"])
        got = members(out)
        for rel in ("CHANGELOG.md", era_units.CREDITS, "src/units.rndf", "text/units.csv", "mod.toml"):
            self.assertEqual(got[rel], self.text(rel), rel)
        want = self.root / "want-README.md"            # (written as `write` writes a text: the PC's own line ends)
        want.write_text("\n".join(README_CUT[t] for t in MODDER_TEXTS) + "\n", encoding="utf-8")
        self.assertEqual(got["README.md"].decode("utf-8").splitlines(), want.read_text(encoding="utf-8").splitlines())
        self.assertEqual(got["README.md"], want.read_bytes())

    def test_every_readme_of_his_is_cut_and_no_other_text(self):
        """The class of his READMEs (package.is_readme): README.md at the top and any README of his in the mod's
        folders (readme.txt, README with no ending, README-fr.md), each folder path cut to its own name, his line
        ends and a UTF-8 mark at the start kept; the same path in CHANGELOG.md, LICENSE, a note of his or a picture
        called readme goes out byte for byte; a README in this PC's own code page (Notepad's "ANSI") is cut the same,
        every other byte as it was (the export fix's review, defect 5: it went out as written before); a README with
        no folder path in it goes out byte for byte."""
        line = f"Made from {PC}\\models\\tank.glb, and docs\\turret.md tells how."
        cut = "Made from tank.glb, and docs\\turret.md tells how."
        readmes = {"README.md": (line + "\r\n").encode("utf-8"),
                   "files/notes/readme.txt": ("﻿" + line + "\n").encode("utf-8"),
                   "files/docs/README": (line + "\n").encode("utf-8"),
                   "src/README-fr.md": ("Fait depuis /home/jane/mods/tank.glb.\n").encode("utf-8"),
                   "files/latin/README.TXT": f"Fait sur {PC}\\x\\\xe9t\xe9.glb\n".encode("cp1252")}
        for rel, data in readmes.items():
            self.write(rel, data)
        others = {"CHANGELOG.md": (line + "\n").encode("utf-8"), "LICENSE": (line + "\n").encode("utf-8"),
                  "files/notes/made.md": (line + "\n").encode("utf-8"), "files/notes/readme.png": b"\x89PNG " + line.encode(),
                  "files/plain/README.md": b"Nothing here names a folder: docs\\turret.md, and/or /r/ruse.\n"}
        for rel, data in others.items():
            self.write(rel, data)
        cleaned, kinds, home_in, cuts = [], {}, [], {}
        with mock.patch.object(package, "_ansi", lambda: "cp1252"):     # (this PC's own code page: Windows-1252)
            out = package.pack(self.mod, self.root / "out", cleaned=cleaned, kinds=kinds, home_in=home_in, home=PC,
                               cuts=cuts)
        got = members(out)
        self.assertEqual(got["README.md"], (cut + "\r\n").encode("utf-8"))
        self.assertEqual(got["files/notes/readme.txt"], ("﻿" + cut + "\n").encode("utf-8"))
        self.assertEqual(got["files/docs/README"], (cut + "\n").encode("utf-8"))
        self.assertEqual(got["src/README-fr.md"], "Fait depuis tank.glb.\n".encode("utf-8"))
        self.assertEqual(got["files/latin/README.TXT"], b"Fait sur \xe9t\xe9.glb\n")
        for rel, data in others.items():
            self.assertEqual(got[rel], data, rel)
        self.assertEqual(sorted(cleaned), sorted(readmes))
        self.assertEqual({k for k, v in kinds.items() if v == "readme"}, set(readmes))
        self.assertEqual(cuts["src/README-fr.md"], [("/home/jane/mods/tank.glb.", "tank.glb.")])
        self.assertEqual(cuts["files/latin/README.TXT"], [(f"{PC}\\x\\\xe9t\xe9.glb", "\xe9t\xe9.glb")])
        self.assertEqual(sorted(home_in), ["CHANGELOG.md", "LICENSE", "files/notes/made.md"])
        for rel in readmes:                                  # (his own files as he wrote them)
            self.assertEqual(self.text(rel), readmes[rel], rel)

    def test_a_readme_in_another_text_encoding_is_cut_the_same_every_other_byte_as_it_was(self):
        """The export fix's review, defect 5: a README saved as "Unicode" (UTF-16 with its mark) or in this PC's own
        code page (Notepad's "ANSI": Windows-1252, -1251, Shift-JIS on a Japanese PC) went out with the user's path
        whole, and Export said nothing (on 1b9853b5 and e9a092c3). Each is read in its own encoding and cut as a UTF-8
        one is; only what goes of each path is taken out of its bytes, every other byte as it was (its mark, its line
        ends, a Shift-JIS letter whose second byte is a backslash's: 表). Each answer is written out here by hand."""
        line = "Fait sur C:\\Users\\J\u00e9r\u00f4me, depuis C:\\models\\tank.glb.\r\n"
        cut = "Fait sur , depuis tank.glb.\r\n"
        kanji = ("\u8868\u793a: C:\\Users\\\u5c71\u7530 \u592a\u90ce\\\u8868.glb \u3068 C:\\Users\\\u5c71\u7530 "
                 "\u592a\u90ce \u3067\u4f5c\u3063\u305f\u3002\n")
        kanji_cut = "\u8868\u793a: \u8868.glb \u3068  \u3067\u4f5c\u3063\u305f\u3002\n"
        self.assertIn(b"\x95\x5c", kanji.encode("cp932"))       # (表: its second byte is a backslash's)
        cases = {   # (where, its bytes, what goes out, this PC's own code page)
            "README.md": (codecs.BOM_UTF16_LE + line.encode("utf-16-le"),
                          codecs.BOM_UTF16_LE + cut.encode("utf-16-le"), "cp1252"),
            "files/be/README.txt": (codecs.BOM_UTF16_BE + line.encode("utf-16-be"),
                                    codecs.BOM_UTF16_BE + cut.encode("utf-16-be"), "cp1252"),
            "files/w32/README.txt": (codecs.BOM_UTF32_LE + line.encode("utf-32-le"),
                                     codecs.BOM_UTF32_LE + cut.encode("utf-32-le"), "cp1252"),
            "files/ansi/README.txt": (line.encode("cp1252"), cut.encode("cp1252"), "cp1252"),
            "files/ru/README.md": ("\u0421\u0434\u0435\u043b\u0430\u043d\u043e \u043d\u0430 C:\\Users\\"
                                   "\u0418\u0432\u0430\u043d.\n".encode("cp1251"),
                                   "\u0421\u0434\u0435\u043b\u0430\u043d\u043e \u043d\u0430 .\n".encode("cp1251"),
                                   "cp1251"),
            "files/jp/README.md": (kanji.encode("cp932"), kanji_cut.encode("cp932"), "cp932")}
        for rel, (data, want, ansi) in cases.items():
            with self.subTest(rel=rel):
                self.write(rel, data)
                unread = []
                with mock.patch.object(package, "_ansi", lambda a=ansi: a):
                    got = package.readme_paths_out(self.mod / rel, rel, (), unread)
                self.assertIsNotNone(got)
                self.assertEqual(got[0], want)
                self.assertEqual(unread, [])
                self.assertEqual(self.text(rel), data)            # (his own file as he wrote it)
        self.assertEqual(package.readme_paths_out(self.mod / "README.md", "README.md")[1],
                         [("C:\\Users\\J\u00e9r\u00f4me", ""), ("C:\\models\\tank.glb.", "tank.glb.")])

    def test_a_readme_export_can_t_read_goes_out_as_written_and_is_named(self):
        """A README no encoding above reads (not UTF-8, no mark, and this PC's own code page refuses a byte of it, or
        is UTF-8 itself) goes out byte for byte, and pack's `unread` names it, so Export says so (never silent: the
        review's defect 5); one Export reads, and one with nothing to cut, aren't named."""
        his = "Fait sur C:\\Users\\J\u00e9r\u00f4me, merci.\n".encode("cp1252")
        self.write("README.md", his)
        self.write("files/odd/README.txt", b"Made on C:\\Users\\jane \x81\x8d\n")   # (two bytes Windows-1252 hasn't)
        self.write("files/plain/README.md", b"Nothing to cut here.\n")
        unread, home_in = [], []
        with mock.patch.object(package, "_ansi", lambda: None):   # (a PC whose own encoding is UTF-8: Linux, a Deck)
            out = package.pack(self.mod, self.root / "out", unread=unread, home_in=home_in, home="C:\\Users\\jane")
        got = members(out)
        self.assertEqual((got["README.md"], got["files/odd/README.txt"]), (his, self.text("files/odd/README.txt")))
        self.assertEqual(sorted(unread), ["README.md", "files/odd/README.txt"])
        self.assertEqual(home_in, ["files/odd/README.txt"])     # (and it names this PC's home folder: said too)
        unread = []
        with mock.patch.object(package, "_ansi", lambda: "cp1252"):
            out = package.pack(self.mod, self.root / "out2", unread=unread)
        self.assertEqual(unread, ["files/odd/README.txt"])
        self.assertEqual(members(out)["README.md"], b"Fait sur , merci.\n")   # (read in this PC's own: cut)

    def test_this_pc_s_home_folder_is_found_in_every_text_encoding(self):
        """home_named (Export's line for his texts that go out as written): this PC's home folder is found in a text
        of his in UTF-8, UTF-16 and this PC's own code page; on 1b9853b5 and e9a092c3 a name with é in it, or any name
        in UTF-16, wasn't found, and Export said nothing (the review's defect 5)."""
        home = "C:\\Users\\J\u00e9r\u00f4me"
        named = f"Notes from {home}\\AppData\\x.\n"
        self.write("CHANGELOG.md", codecs.BOM_UTF16_LE + named.encode("utf-16-le"))
        self.write("files/notes/made.txt", named.encode("cp1252"))
        self.write("files/notes/plain.txt", named.encode("utf-8"))
        self.write("files/notes/other.txt", b"Notes from C:\\Users\\someone\\x.\n")
        home_in = []
        with mock.patch.object(package, "_ansi", lambda: "cp1252"):
            package.pack(self.mod, self.root / "out", home_in=home_in, home=home)
        self.assertEqual(sorted(home_in), ["CHANGELOG.md", "files/notes/made.txt", "files/notes/plain.txt"])

    def test_his_readme_s_paths_to_a_user_s_own_folder_go_whole(self):
        """pack: a README path that ends at a user's own folder goes whole (the owner, 2026-11-13: "Probably take the
        username path out"), this PC's user's name known exactly from its home folder (`home`); `cuts` lists each, its
        name "", beside a path cut to its name as before; his README in the mod as he wrote it."""
        mine = "C:\\Users\\kim lee\\AppData\\Local\\RUSE Mod Platform"
        readme = ("Made on C:\\Users\\Jane Doe by me, on C:\\Users\\kim lee too.\n"
                  "From C:\\models\\tank.glb, and docs\\turret.md tells how.\n")
        self.write("README.md", readme)
        cuts = {}
        out = package.pack(self.mod, self.root / "out", cuts=cuts, home=mine)
        self.assertEqual(cuts, {"README.md": [("C:\\Users\\Jane Doe", ""), ("C:\\Users\\kim lee", ""),
                                              ("C:\\models\\tank.glb,", "tank.glb,")]})
        got = members(out)["README.md"].decode("utf-8")
        self.assertEqual(got.splitlines(), ["Made on  by me, on  too.", "From tank.glb, and docs\\turret.md tells how."])
        for name in ("Jane", "Doe", "kim", "lee", "Users"):
            self.assertNotIn(name, got, name)
        self.assertEqual(self.text("README.md").decode("utf-8").splitlines(), readme.splitlines())

    def test_a_record_from_any_system_names_only_its_file(self):
        """F1 of the export recheck, as a class: the record's "from" is the file's own name wherever the folder was
        (no list of known folders), its other bytes as they were."""
        for i, made in enumerate(("/var/home/jane/.local/share/ruse-mod-platform/horse_squad/horse-squad-rifle.glb",
                                  "/Volumes/Jane Drive/models/horse-squad-rifle.glb",
                                  "/opt/models/horse-squad-rifle.glb", "/data/jane/horse-squad-rifle.glb",
                                  "\\\\?\\C:\\Users\\jane\\horse-squad-rifle.glb",
                                  "file:///home/jane/horse-squad-rifle.glb",
                                  "E:\\Mods & Models\\Jane's (2026)\\horse-squad-rifle.glb")):
            rel = f"files/models/Descriptor_Unit_X{i}.json"
            self.write(rel, json.dumps({"from": made, "size": 1.0, "report": {"file": "horse-squad-rifle.glb"}},
                                       indent=1))
        got = members(package.pack(self.mod, self.root / "out"))
        for i in range(7):
            rel = f"files/models/Descriptor_Unit_X{i}.json"
            packed = json.loads(got[rel])
            self.assertEqual(packed["from"], "horse-squad-rifle.glb", rel)
            self.assertEqual(got[rel], self.text(rel).replace(
                json.dumps(json.loads(self.text(rel))["from"]).encode(), b'"horse-squad-rifle.glb"'), rel)

    def test_a_model_the_modder_made_keeps_its_own_names(self):
        """A .glb of his (from Blender: no scenery source the Studio wrote) goes out byte for byte, a mesh name
        holding a path among it; a scenery model whose mesh name the modder changed keeps his name, its source the
        file's name only."""
        g = _Glb()
        g.doc["meshes"] = [{"name": "C:\\Users\\jane\\turret", "primitives": [{"attributes": {"POSITION": g.packed(
            struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), 3, "VEC3", 5126, low=[0, 0, 0], high=[1, 1, 0])}}]}]
        g.doc["asset"]["generator"] = "Khronos glTF Blender I/O"
        his = self.write("files/models/Descriptor_Unit_Y.glb", g.to_bytes())
        made = glb_naming("D:\\maps\\a\\files\\assets\\Rock\\Rock.glb (far)")
        doc, binary = glb_document(made)
        doc["meshes"][0]["name"] = "his rock/far"
        js = json.dumps(doc, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        renamed = (struct.pack("<4sII", b"glTF", 2, 28 + len(js) + len(binary)) + struct.pack("<I4s", len(js), b"JSON")
                   + js + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)
        self.write("files/assets/Rock/Rock_far.glb", renamed)
        got = members(package.pack(self.mod, self.root / "out"))
        self.assertEqual(got["files/models/Descriptor_Unit_Y.glb"], his.read_bytes())
        doc, _binary = glb_document(got["files/assets/Rock/Rock_far.glb"])
        self.assertEqual((doc["meshes"][0]["name"], doc["asset"]["extras"]["rusemod_version"]),
                         ("his rock/far", "Rock.glb (far)"))

    def test_a_map_import_record_names_only_its_folders(self):
        """maps/<Pack>/import.toml as the real-place import writes it (rusemod.placebase._import_toml, on the
        importer's branch): [base] folder, engine_run and engine_code name only their folders; every other line as it
        was. An import.toml the import didn't write goes out as it is."""
        def q(v):
            return json.dumps(v, ensure_ascii=False)
        lines = ["# The import's record (rusemod.placebase): what this map was made from, by what, with what choice.",
                 "# The build does not read it; the Studio's Import panel will.", "", "[place]", 'slug = "utah"',
                 f"note = {q('see C:/Users/jane/x for how')}", "", "[base]",
                 f"folder = {q(PC + chr(92) + 'places' + chr(92) + 'utah' + chr(92) + 'base-full')}",
                 'manifest_sha256 = "f7"', f"files = {q(json.dumps({'heights': 'ab'}))}",
                 f"engine_run = {q('/var/home/jane/terraform/builds/tf-base-land6')}",
                 f"engine_code = {q('D:/RUSE-2.0/scratch/terraform/run.py')}", "", "[made]", 'pack = "Utah"',
                 'importer = "rusemod.placebase"', "", "[said]", f"notes = [{q('heights from C:/data/dem.tif')}]", ""]
        record = self.write("maps/Utah/import.toml", "\n".join(lines))
        other = self.write("maps/Mine/import.toml", f'[base]\nfolder = {q(PC)}\n')
        kinds = {}
        got = members(package.pack(self.mod, self.root / "out", kinds=kinds))
        self.assertEqual(kinds, {"maps/Utah/import.toml": "import"})
        self.assertEqual(got["maps/Mine/import.toml"], other.read_bytes())
        want = record.read_bytes().decode("utf-8").splitlines(keepends=True)
        for k, name in ((8, 'folder = "base-full"'), (11, 'engine_run = "tf-base-land6"'),
                        (12, 'engine_code = "run.py"')):
            want[k] = name + want[k][len(want[k].rstrip("\r\n")):]
        self.assertEqual(got["maps/Utah/import.toml"].decode("utf-8"), "".join(want))
        self.assertEqual(tomllib.loads(got["maps/Utah/import.toml"].decode("utf-8"))["base"]["folder"], "base-full")


class OnTheMadeUpGame(WithMod):
    """The Horse Squad and an era unit added on one player's PC, exported, and opened in another player's Studio (his
    Launcher library's add, then Edit an installed mod)."""

    def setUp(self):
        super().setUp()
        lib = era_library(Path(tempfile.mkdtemp(dir=self.tmp.name)))
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(lib)})
        patcher.start()
        self.addCleanup(patcher.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")

    def add(self, api) -> dict:
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(self.rifle, self.heavy)}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            return finished(api, api.horse_squad_add(0, 10, "Cavalry", 7, group="new")["job"])

    def exported(self):
        """A mod with the Liberty, the Horse Squad and a model record naming this PC's platform folder, exported."""
        folder = Path(self.api.new_mod("Shared")["current"])
        self.liberty = self.api.era_unit_add(LIBERTY, 0, 10)["address"]
        view = self.add(self.api)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.unit = view["result"]["address"]
        record = folder / "files" / "models" / (self.unit.rsplit("/", 1)[-1] + ".json")
        record.parent.mkdir(parents=True, exist_ok=True)
        made = self.home / horse_squad.FOLDER / self.rifle.name
        record.write_text(json.dumps({"from": str(made), "size": 1.0, "report": {"file": made.name}}, indent=1),
                          encoding="utf-8")
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "With the Generic Horse.")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        return folder, record, Path(view["result"]["path"]), view

    def test_the_export_carries_the_credits_and_the_record_and_no_folder_of_his_pc(self):
        folder, record, export, view = self.exported()
        got = members(export)
        self.assertEqual(json.loads(got[era_units.INDEX]), {LIBERTY: self.liberty, KEY: self.unit})
        self.assertIn(HIS_LINE.encode(), got[era_units.CREDITS])
        self.assertIn(LIBERTY_LINE.encode(), got[era_units.CREDITS])
        home = str(self.home)
        for name, data in got.items():
            for form in (home, home.replace("\\", "/"), json.dumps(home)[1:-1]):
                self.assertNotIn(form.encode("utf-8"), data, name)
        self.assertEqual(json.loads(got[record.relative_to(folder).as_posix()])["from"], self.rifle.name)
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["from"],
                         str(self.home / horse_squad.FOLDER / self.rifle.name))   # his own record keeps its folder
        said = [ln for ln in view["lines"] if ln.startswith("In the exported file,")]
        self.assertEqual(said, ["In the exported file, these model records name only the file each model was made "
                                "from, not the folder on your PC it is in; nothing else in them changed: "
                                f"{record.relative_to(folder).as_posix()}."])
        self.api.set_pref("lang", "fr")
        worded = [ln for ln in self.api.job(view["id"])["lines"] if "ces fiches de modèle" in ln]
        self.assertEqual(len(worded), 1)
        library = self.home / "library" / package.info_of(folder)["id"]   # (Export puts it in his Launcher's library)
        self.assertEqual((library / era_units.INDEX).read_bytes(), got[era_units.INDEX])
        self.assertEqual((library / era_units.CREDITS).read_bytes(), got[era_units.CREDITS])

    def test_his_readme_s_folders_go_his_description_goes_out_as_written_and_the_export_says_both(self):
        """A README and a description of his naming folders of his PC (his home among them): Export cuts the README's
        folder path to its file's name (the owner, 2026-11-13: "cut to file name") and says so, his README in the mod
        as he wrote it; the description goes out as written ("yes only warn"), and Export says it names his home
        folder; both lines in his language."""
        folder = Path(self.api.new_mod("Shared")["current"])
        readme = f"Made from {PC}\\models\\tank.glb, and docs\\turret.md tells how.\nPlan B:/C\n"
        (folder / "README.md").write_bytes(readme.encode("utf-8"))
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        with mock.patch("pathlib.Path.home", return_value=Path(PC)):
            view = finished(self.api, self.api.export_mod("1.0.0", "a modder", f"Plan B:/C from {PC}\\x.glb")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        got = members(Path(view["result"]["path"]))
        self.assertEqual(got["README.md"], b"Made from tank.glb, and docs\\turret.md tells how.\nPlan B:/C\n")
        self.assertEqual((folder / "README.md").read_bytes(), readme.encode("utf-8"))   # (his own, as he wrote it)
        self.assertEqual(got["mod.toml"], (folder / "mod.toml").read_bytes())
        self.assertIn(f"Plan B:/C from {PC}\\x.glb", tomllib.loads(got["mod.toml"].decode("utf-8"))["mod"]
                      .get("description", ""))
        said = [ln for ln in view["lines"] if ln.startswith("These files of the mod name your PC's home folder")]
        self.assertEqual(said, [f"These files of the mod name your PC's home folder ({PC}) and go out as they are, "
                                "since Export never changes what you wrote: change them in the mod if that shouldn't "
                                "be shared: mod.toml."])
        cut = [ln for ln in view["lines"] if ln.startswith("In the exported file,")]
        self.assertEqual(cut, ["In the exported file, each folder path in these README files of yours is cut to its "
                               "own name, every other word as you wrote it; the files in your mod stay as they are: "
                               f"README.md ({PC}\\models\\tank.glb \u2192 tank.glb)."])
        self.api.set_pref("lang", "ger")
        lines = self.api.job(view["id"])["lines"]
        self.assertEqual(len([ln for ln in lines if "Benutzerordner" in ln]), 1)
        self.assertEqual([ln for ln in lines if ln.startswith("In der exportierten Datei ist jeder Ordnerpfad")],
                         ["In der exportierten Datei ist jeder Ordnerpfad in diesen README-Dateien von Ihnen auf seinen "
                          "eigenen Namen gekürzt, jedes andere Wort so, wie Sie es geschrieben haben; die Dateien in "
                          f"Ihrem Mod bleiben, wie sie sind: README.md ({PC}\\models\\tank.glb \u2192 tank.glb)."])

    def test_export_says_which_paths_to_a_user_s_own_folder_it_took_out(self):
        """Export's list of cuts says a path that ends at a user's own folder was taken out completely (a line of its
        own), in his language; a path cut to its name keeps its own line, as before."""
        folder = Path(self.api.new_mod("Shared")["current"])
        readme = "Made on C:\\Users\\Jane Doe by me.\nFrom C:\\models\\tank.glb.\n"
        (folder / "README.md").write_bytes(readme.encode("utf-8"))
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        with mock.patch("pathlib.Path.home", return_value=Path(PC)):
            view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(members(Path(view["result"]["path"]))["README.md"], b"Made on  by me.\nFrom tank.glb.\n")
        said = [ln for ln in view["lines"] if ln.startswith("In the exported file, each")]
        self.assertEqual(said, [
            "In the exported file, each folder path in these README files of yours is cut to its own name, every other "
            "word as you wrote it; the files in your mod stay as they are: README.md (C:\\models\\tank.glb \u2192 "
            "tank.glb).",
            "In the exported file, each path in these README files of yours that ends at a user's own folder, and so "
            "names the user, is taken out completely; every other word stays as you wrote it, and the files in your "
            "mod stay as they are: README.md (C:\\Users\\Jane Doe)."])
        self.api.set_pref("lang", "ger")
        lines = self.api.job(view["id"])["lines"]
        self.assertEqual([ln for ln in lines if ln.startswith("In der exportierten Datei ist jeder Pfad")],
                         ["In der exportierten Datei ist jeder Pfad in diesen README-Dateien von Ihnen, der am eigenen "
                          "Ordner eines Benutzers endet und so den Benutzer nennt, ganz entfernt; jedes andere Wort "
                          "bleibt so, wie Sie es geschrieben haben, und die Dateien in Ihrem Mod bleiben, wie sie "
                          "sind: README.md (C:\\Users\\Jane Doe)."])

    def test_export_says_which_readmes_it_can_t_read(self):
        """A README of his that Export can't read goes out as he wrote it, and Export says so on a line of its own, in
        his language (the export fix's review, defect 5: before, it went out with its paths whole and nothing said)."""
        folder = Path(self.api.new_mod("Shared")["current"])
        his = b"Made on C:\\Users\\jane \x81\x8d by me.\n"           # (neither UTF-8 nor Windows-1252)
        (folder / "README.md").write_bytes(his)
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        with mock.patch("pathlib.Path.home", return_value=Path(PC)), \
                mock.patch.object(package, "_ansi", lambda: "cp1252"):
            view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(members(Path(view["result"]["path"]))["README.md"], his)
        said = [ln for ln in view["lines"] if ln.startswith("Export can't read")]
        self.assertEqual(said, ["Export can't read the text of these README files of yours, so they go out as you "
                                "wrote them, with any folder path or user's name in them; save them as UTF-8 and "
                                "export again to have those taken out: README.md."])
        self.api.set_pref("lang", "ger")
        lines = self.api.job(view["id"])["lines"]
        self.assertEqual([ln for ln in lines if ln.startswith("Der Export kann den Text")],
                         ["Der Export kann den Text dieser README-Dateien von Ihnen nicht lesen, daher gehen sie so "
                          "hinaus, wie Sie sie geschrieben haben, mit jedem Ordnerpfad und Benutzernamen darin; "
                          "speichern Sie sie als UTF-8 und exportieren Sie erneut, damit diese entfernt werden: "
                          "README.md."])

    def test_another_player_s_studio_knows_its_era_units_are_in_the_mod(self):
        _folder, _record, export, _view = self.exported()
        other_home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        other = StudioApi(index_path=self.index, game_dir=self.game, home=other_home, instances=other_home / "copies")
        info, _replaced = Library(other_home / "library").add(export)
        copy = Path(other.edit_installed(info["id"], "Shared (my copy)")["path"])
        self.assertEqual(json.loads((copy / era_units.INDEX).read_text(encoding="utf-8")),
                         {LIBERTY: self.liberty, KEY: self.unit})
        self.assertEqual([u["added"] for u in other.era_units_list("WWII")["units"] if u["key"] == KEY], [self.unit])
        self.assertEqual([u["added"] for u in other.era_units_list("WWI")["units"] if u["key"] == LIBERTY],
                         [self.liberty])
        self.assertEqual(other.era_unit_page(KEY, "us")["added"], self.unit)
        with self.assertRaisesRegex(StudioError, "already in this mod"):
            other.horse_squad_add(0, 10, "Cavalry", 7, group="new")       # Add says it's in the mod already
        self.assertEqual(other.era_unit_remove(KEY)["removed"], self.unit)  # and Take it out works there
        self.assertNotIn(self.unit, {u["address"] for u in other.units("us")["units"] if u.get("new")})
        self.assertEqual(json.loads((copy / era_units.INDEX).read_text(encoding="utf-8")), {LIBERTY: self.liberty})
        credits = (copy / era_units.CREDITS).read_text(encoding="utf-8")
        self.assertNotIn(HIS_LINE, credits)
        self.assertIn(LIBERTY_LINE, credits)

    def test_a_record_naming_only_its_file_is_never_looked_for_where_the_studio_runs(self):
        folder, record, export, _view = self.exported()
        other_home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        other = StudioApi(index_path=self.index, game_dir=self.game, home=other_home, instances=other_home / "copies")
        info, _replaced = Library(other_home / "library").add(export)
        copy = Path(other.edit_installed(info["id"], "Shared (my copy)")["path"])
        his = copy / record.relative_to(folder)
        self.assertEqual(json.loads(his.read_text(encoding="utf-8"))["from"], self.rifle.name)
        (copy / "files" / "models" / (self.unit.rsplit("/", 1)[-1] + ".glb")).write_bytes(b"glTF")
        here = Path(tempfile.mkdtemp(dir=self.tmp.name))
        (here / self.rifle.name).write_bytes(b"another file of the same name")
        was = os.getcwd()
        os.chdir(here)                                       # (a file of that name where the Studio runs)
        self.addCleanup(os.chdir, was)
        self.assertFalse(other.model_sizes(self.unit, "us")["resizable"])
        with self.assertRaisesRegex(StudioError, "isn't there any more"):
            other.model_resize(self.unit, 1.2)
        with self.assertRaisesRegex(StudioError, "isn't there any more"):
            other.model_place(self.unit, [0, 0, 1])


if __name__ == "__main__":
    unittest.main()
