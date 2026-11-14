"""Review of the Horse Squad's whole Studio path with the real builder (rusemod.horsesquad, never a stand-in), judged on
the files written, exported and opened again: the Units tab's Add to my mod (StudioApi.horse_squad_add), Export mod
(package.pack through export_mod), and the exported file opened in a second, fresh platform folder as another player
opens it (the Launcher library's add, then Edit an installed mod).

Needs the game (RUSE_GAME), the Studio's game index (RUSE_GAME_INDEX or RUSE_STUDIO_INDEX; this PC's by default) and the
two horse-and-rider files of the copy that passed in the game (RUSE_HORSE_FIXES3 or RUSE_HORSE_SQUAD_GLBS; this PC's
fixes3 folder by default); skipped without them. The game and the index are only read.

What it holds (the owner, 2026-11-12, on the Horse Squad: "Yes, like era units": off until a modder adds it, made on
his own PC from his own game when added, "your name, sneadtristen6, in that mod's credits"):
- SOUND, kept: the Studio's Add with the real builder gives the mod the passed copy's route gives (horse-studio2's own
  calls: new_unit, Import model, Import model for the heavy-weapon soldier), byte for byte, besides its era record, its
  credit line, its mod.toml and each model record's "from" and "report.file" (the platform folder's copy).
- FINDINGS, failing on 07a688b5 by design until fixed:
  - its credit line and its era record don't go out with Export, so another player's Studio says the Horse Squad isn't
    in the mod (its Add then makes a second one, its Take out is refused);
  - Resize and Move are off in another player's Studio, even one whose own platform folder holds the same two files:
    the exported records name the first player's folder;
  - the exported records carry the first player's own folder (in the app: C:\\Users\\<his Windows name>\\AppData\\...);
  - the exported models carry the game's own textures, pixel for pixel, though the Horse Squad is made on each
    player's PC because the game's files can't go in a download (ruse_studio/horse_squad.py);
  - a refusal of the builder is said in English inside the Studio's translated words."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from ruse_studio import era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ.get("RUSE_GAME_INDEX") or os.environ.get("RUSE_STUDIO_INDEX")
             or "D:/RUSE-2.0/scratch/modelgaps/game-index.sqlite")
FIXES3 = Path(os.environ.get("RUSE_HORSE_FIXES3") or os.environ.get("RUSE_HORSE_SQUAD_GLBS")
              or "D:/RUSE-2.0/scratch/animmodels/fixes3")
RIFLE, HEAVY = FIXES3 / "horse-squad-rifle-death.glb", FIXES3 / "horse-squad-bazooka-death.glb"
KEY, SQUAD = horse_squad.KEY, horse_squad.SQUAD
READY = GAME is not None and GAME.is_dir() and INDEX.is_file() and RIFLE.is_file() and HEAVY.is_file()
WHY_SKIPPED = ("RUSE_GAME names no game folder, or the Studio's game index or the two horse-and-rider files of the copy "
               "that passed in the game aren't there")


def finished(api, job: str, most: float = 1800) -> dict:
    end = time.monotonic() + most
    while time.monotonic() < end:
        view = api.job(job)
        if view["state"] != "running":
            return view
        time.sleep(0.2)
    raise AssertionError(f"job {job} still running after {most} s")


def tree(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


def added(api, mod_name: str) -> tuple[Path, str]:
    """A new mod with the Horse Squad added as the Units tab adds it, the real builder making its two files: (the mod,
    the unit's address)."""
    folder = Path(api.new_mod(mod_name)["current"])
    page = api.era_unit_page(KEY, "us")
    view = finished(api, api.horse_squad_add(page["game_nation"], page["factory"], "Generic Horse", 5, None, None, None,
                                             "new")["job"])
    if view["state"] != "done":
        raise AssertionError(f"the Generic Horse wasn't added: {view.get('message')}")
    return folder, view["result"]["address"]


def opened_by_another_player(home: Path, export: Path, copy_name: str):
    """The exported file in another player's fresh platform folder: added to his Launcher library, then opened with
    Edit an installed mod (a copy of his own). Returns (his Studio, the copy's folder)."""
    from rusemod.library import Library
    api = StudioApi(index_path=INDEX, game_dir=GAME, home=home)
    info, _replaced = Library(home / "library").add(export)
    opened = api.edit_installed(info["id"], copy_name)
    return api, Path(opened["path"])


@unittest.skipUnless(READY, WHY_SKIPPED)
class TheWholePath(unittest.TestCase):
    """One player adds the Horse Squad with the real builder and exports his mod; another opens it (his platform folder
    without the Horse Squad's files, and one where he added it to a mod of his own first)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="review-path-"))
        env = mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(cls.tmp / "platform")})  # (the build's cache)
        env.start()
        cls.addClassCleanup(env.stop)
        cls.addClassCleanup(shutil.rmtree, cls.tmp, True)
        cls.home = cls.tmp / "first"
        cls.api = StudioApi(index_path=INDEX, game_dir=GAME, home=cls.home)
        cls.mod, cls.unit = added(cls.api, "Cavalry")
        cls.export_job = finished(cls.api, cls.api.export_mod("1.0.0", "a modder", "With the Generic Horse.")["job"])
        cls.export = Path(cls.export_job["result"]["path"]) if cls.export_job["state"] == "done" else None
        # another player, his platform folder without the Horse Squad's files
        cls.other, cls.copy = opened_by_another_player(cls.tmp / "second", cls.export, "Cavalry (my copy)")
        # another player who added the Horse Squad to a mod of his own first: his platform folder has the same files
        third = cls.tmp / "third"
        cls.third = StudioApi(index_path=INDEX, game_dir=GAME, home=third)
        added(cls.third, "My own")
        cls.third, cls.third_copy = opened_by_another_player(third, cls.export, "Cavalry (his copy)")

    def test_the_add_gives_the_passed_copy_s_files(self):
        """SOUND (kept): the real builder's two files are the passed copy's, byte for byte, and the Studio's Add gives
        the mod the files horse-studio2's own calls give with them: the era record, the credit line and mod.toml
        besides, and each model record's "from" (the platform folder's copy) and "report.file" (its name)."""
        kept = self.home / horse_squad.FOLDER
        self.assertEqual({p.name: p.read_bytes() for p in kept.iterdir()},
                         {"horse-squad-rifle.glb": RIFLE.read_bytes(), "horse-squad-bazooka.glb": HEAVY.read_bytes()})
        by_hand = Path(self.api.new_mod("By hand")["current"])
        unit = self.api.new_unit(SQUAD, "Generic Horse", 5, group="new")["address"]
        self.api.model_import(unit, str(RIFLE))
        self.api.model_import(unit, str(HEAVY), kind="bazooka")
        self.assertEqual(unit, self.unit)
        mine = tree(self.mod)
        theirs = tree(by_hand)
        self.assertEqual(json.loads(mine.pop(era_units.INDEX)), {KEY: unit})
        self.assertIn("sneadtristen6", mine.pop(era_units.CREDITS).decode("utf-8"))
        for t in (mine, theirs):
            t.pop("mod.toml")   # (each mod's own id, name, and the export's version, author and game build)
        self.assertEqual(sorted(mine), sorted(theirs))
        tail = unit.rsplit("/", 1)[-1]
        for stem, file, made in ((tail, RIFLE, "horse-squad-rifle.glb"),
                                 (f"{tail}@bazooka", HEAVY, "horse-squad-bazooka.glb")):
            name = f"files/models/{stem}.json"
            a, b = json.loads(mine.pop(name)), json.loads(theirs.pop(name))
            self.assertEqual((a.pop("from"), b.pop("from")), (str(kept / made), str(file)))
            self.assertEqual((a["report"].pop("file"), b["report"].pop("file")), (made, file.name))
            self.assertEqual(a, b)
        self.assertEqual([n for n in mine if mine[n] != theirs[n]], [])

    def test_his_credit_and_its_record_go_out_with_the_export(self):
        """FINDING (R2): Export packs package.TOP_FILES and src/, text/, files/, maps/, scripts/ only, so the mod's
        CREDITS-era-units.md (the owner's "your name, sneadtristen6, in that mod's credits") and era_units.json (what
        tells the Units tab the Horse Squad is in the mod) stay behind: nothing in the exported file credits him."""
        self.assertEqual(self.export_job["state"], "done", self.export_job.get("message"))
        with zipfile.ZipFile(self.export) as z:
            names = z.namelist()
            credited = [n for n in names if b"Generic Horse (WWII, USA): by sneadtristen6" in z.read(n)]
        self.assertIn(era_units.CREDITS, names)
        self.assertIn(era_units.INDEX, names)
        self.assertNotEqual(credited, [])

    def test_another_player_s_studio_knows_the_horse_squad_is_in_the_mod(self):
        """FINDING (R2): opened by another player, the Horse Squad is in the mod (its unit, both models, 25
        animations), but his Units tab lists it as not added: its page offers Add to my mod (refused with the page's
        name, "There's already a unit called Descriptor_Unit_Horse_Squad"; with another name it makes a second Horse
        Squad) and never Take it out of my mod (refused: "horse-squad: not in this mod")."""
        self.assertIn(self.unit, {u["address"] for u in self.other.units("us")["units"] if u.get("new")})
        rows = {r["kind"]: r for r in self.other.look(self.unit)["kinds"]}
        self.assertEqual((rows["fusilier"]["own"], rows["bazooka"]["own"], rows["bazooka"]["same_bones"]),
                         (True, True, True))
        listed = [u for u in self.other.era_units_list("WWII")["units"] if u["key"] == KEY]
        self.assertEqual([u["added"] for u in listed], [self.unit])
        self.assertEqual(self.other.era_unit_page(KEY, "us")["added"], self.unit)

    def test_another_player_with_the_same_files_can_resize_and_move_it(self):
        """FINDING (R2): Resize and Move fit the Horse Squad again from the files its model records name (horse_squad.py:
        "the mod's model records name them: Resize and Move fit them again from there"). Exported, the records name the
        first player's platform folder, so in another player's Studio they're off, even when his own platform folder
        holds the very same two files (he added the Horse Squad to a mod of his own): the size box says it can't be
        resized, and Resize names the first player's folder."""
        mine = {p.name: p.read_bytes() for p in (self.third._home / horse_squad.FOLDER).iterdir()}
        first = self.home / horse_squad.FOLDER
        self.assertEqual(mine, {p.name: p.read_bytes() for p in first.iterdir()})
        # (his PC hasn't the first player's platform folder: here, on one PC, it's moved aside while he looks)
        away = first.with_name(first.name + ".elsewhere")
        os.replace(first, away)
        self.addCleanup(os.replace, away, first)
        self.third.choose_mod(str(self.third_copy))
        record = self.third_copy / "files" / "models" / (self.unit.rsplit("/", 1)[-1] + ".json")
        named = json.loads(record.read_text(encoding="utf-8"))["from"]
        self.assertTrue(self.third.model_sizes(self.unit, "us")["resizable"],
                        f"Resize and Move are off in his Studio: the model record names {named}")
        try:
            self.third.model_resize(self.unit, 1.0)
        except StudioError as exc:
            self.fail(f"Resize refused in his Studio: {exc}")

    def test_the_export_carries_no_folder_of_the_maker_s_pc(self):
        """FINDING (privacy): each exported model record's "from" is the absolute path of the platform folder's copy of
        the builder's file. In the app the platform folder is %LOCALAPPDATA%\\RUSE Mod Platform, so every exported mod
        with the Horse Squad carries C:\\Users\\<the modder's Windows name>\\AppData\\Local\\RUSE Mod Platform\\
        horse_squad\\horse-squad-rifle.glb (here: this test's own folder, standing for it)."""
        home = str(self.home)
        forms = {home, home.replace("\\", "/"), json.dumps(home)[1:-1]}
        with zipfile.ZipFile(self.export) as z:
            found = {n: sorted(f for f in forms if f.encode("utf-8") in z.read(n)) for n in z.namelist()}
        self.assertEqual({n: f for n, f in found.items() if f}, {})

    def test_the_export_carries_none_of_the_game_s_own_pictures(self):
        """FINDING (owned copies), with the owner's one exception for now: the Horse Squad is made on each player's PC
        from his own game because "Its models are made from the game's own horse and rifleman, which can't go in a
        download: nothing of it is downloaded" (ruse_studio/horse_squad.py; CLAUDE.md: the tools "never ship the game's
        files"). The exported file, which the Launcher library, Share's .zip and Publish pass on, carries the game's
        own textures pixel for pixel in its two models (the scenery horse's and the US infantry's).
        The owner, 2026-11-12, asked "What should Export do with the Horse Squad's made files?" (his answer in the
        question dialog, as the lead quoted it): "Just the exception for now to the game files being exported is this
        horse squad. horse squad shoul d have a diff picture of a horse. ideally horse squad is just a generic unit
        people can make custom for each country for a ww1 mod or something." So the Horse Squad's two made models
        (the unit the exported era record names for it, and its heavy-weapon soldier's) may carry them, for now. No
        other model in the file may: the game's picture in any other model, under any other unit's name, is still a
        finding (checked below on a copy of the file with one added)."""
        from rusemod.dxt import png_bytes
        from rusemod.gltf import _Glb, _split, glb_views
        from rusemod.models import Library
        from rusemod.png import read_png

        def rgb(w, h, px):
            return bytes(b for i, b in enumerate(px) if i % 4 != 3) if len(px) == w * h * 4 else bytes(px)

        def pictures(raw):
            doc, views = glb_views(raw)
            out = []
            for image in doc.get("images", []):
                w, h, px = read_png(views[image["bufferView"]])
                out.append((w, rgb(w, h, px)))
            return out

        def named_textures(raw):
            doc, _views = glb_views(raw)
            return {(m.get("extras") or {}).get("rusemod_texture") for m in doc.get("materials", [])} - {None}

        made = {f.name: f.read_bytes() for f in (self.home / horse_squad.FOLDER).glob("*.glb")}
        self.assertTrue(set().union(*(named_textures(raw) for raw in made.values())))

        def game_pictures(export: Path) -> list:
            """(model, the game's texture) for each picture of a model in `export` that is the game's own, pixel for
            pixel: against the textures the Horse Squad's made files and every model in the file name."""
            with zipfile.ZipFile(export) as z:
                models = {n: z.read(n) for n in z.namelist() if n.endswith(".glb")}
            textures = set().union(*(named_textures(raw) for raw in [*made.values(), *models.values()]))
            shipped = [(n, w, px) for n, raw in models.items() for w, px in pictures(raw)]
            lib = Library(GAME)
            try:
                game = {}
                for tex in sorted(textures):
                    for width in sorted({w for _n, w, _px in shipped}):
                        got = lib.picture(tex, most=width)
                        if got is not None:
                            game[_split(got[2])[0]] = tex
            finally:
                lib.close()
            return sorted({(n, game[px]) for n, _w, px in shipped if px in game})

        def his_exception(export: Path) -> set:
            """The Horse Squad's two made models in `export`: those of the unit its era record names for it."""
            with zipfile.ZipFile(export) as z:
                record = json.loads(z.read(era_units.INDEX)) if era_units.INDEX in z.namelist() else {}
            tail = str(record.get(KEY) or "").rsplit("/", 1)[-1]
            return {f"files/models/{tail}.glb", f"files/models/{tail}@bazooka.glb"} if tail else set()

        tail = self.unit.rsplit("/", 1)[-1]
        self.assertEqual(his_exception(self.export), {f"files/models/{tail}.glb", f"files/models/{tail}@bazooka.glb"})
        self.assertEqual([p for p in game_pictures(self.export) if p[0] not in his_exception(self.export)], [])
        # strict for every other model: the game's own US infantry picture in another unit's model is a finding
        infantry = "gen\\ww2\\res3d\\units\\us\\infanterie\\tscother_diffusetexture01.tgv"
        lib = Library(GAME)
        try:
            w, h, px = lib.picture(infantry, most=64)
        finally:
            lib.close()
        g = _Glb()
        g.doc["materials"].append({"name": "uniform", "extras": {"rusemod_texture": infantry}, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": g.image(png_bytes(_split(px)[0], w, h), "uniform")}}})
        another = Path(tempfile.mkdtemp(prefix="review-path-another-"))
        self.addCleanup(shutil.rmtree, another, True)
        shutil.copyfile(self.export, another / self.export.name)
        with zipfile.ZipFile(another / self.export.name, "a") as z:
            z.writestr("files/models/Descriptor_Unit_Other_Rifles.glb", g.to_bytes())
        self.assertEqual([p for p in game_pictures(another / self.export.name)
                          if p[0] not in his_exception(another / self.export.name)],
                         [("files/models/Descriptor_Unit_Other_Rifles.glb", infantry)])


@unittest.skipUnless(READY, WHY_SKIPPED)
class TheBuilderRefusing(unittest.TestCase):
    def test_its_refusal_is_said_wholly_in_the_studio_s_language(self):
        """FINDING (words): the builder's own refusal (rusemod.horsesquad.HorseSquadError, 27 places) comes through
        horse_squad_add inside "The Horse Squad can't be made from your game: {0}", whose frame errors.toml translates;
        its own sentence stays English (here: a game folder without the game's packs)."""
        tmp = Path(tempfile.mkdtemp(prefix="review-path-words-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        not_a_game = tmp / "not-a-game"
        (not_a_game / "Data").mkdir(parents=True)
        api = StudioApi(index_path=INDEX, game_dir=not_a_game, home=tmp / "home")
        api.new_mod("Words")
        page = api.era_unit_page(KEY, "us")
        view = finished(api, api.horse_squad_add(page["game_nation"], page["factory"], "Generic Horse", 5, None, None,
                                                 None, "new")["job"])
        self.assertEqual(view["state"], "failed")
        self.assertIn("isn't a R.U.S.E. game folder", view["message"])     # (the builder's own words, in English)
        api.set_pref("lang", "fr")
        said = api.job(view["id"])["message"]
        self.assertTrue(said.startswith("L'Escouade à cheval générique ne peut pas être fabriquée"), said)
        self.assertNotIn("isn't a R.U.S.E. game folder", said)
        self.assertNotIn("The Generic Horse is made from your game's own files", said)


if __name__ == "__main__":
    unittest.main()
