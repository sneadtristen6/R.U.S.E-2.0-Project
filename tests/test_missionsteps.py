"""A mission's three steps (rusemod.missionsteps: LittleGroove's Menu Entry, Load & Files and Text, on his engine's
own code): the packs read as his engine reads them, a built copy's over the game's; the chain's links worded; a
battle map's missing mission script and texts not called broken (none of the game's has them); and, when the game is
here, every shipped mission read through the Studio."""
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat
from rusemod import missionsteps
from ruse_mod_engine import scenario_chain as chain_mod

WORDS = tomllib.loads((Path(__file__).parents[1] / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
# every way a link can stand (missionsteps._why of what scenario_chain.walk makes)
WHYS = ("scenario_file_ok", "scenario_file_missing", "scenario_cluster_ok", "scenario_cluster_missing",
        "cluster_scenario_ok", "cluster_scenario_missing", "script_ok", "script_missing", "script_unknown", "dico_ok",
        "dico_missing", "optional", "dico_langs_ok", "terrain_cluster_ok", "terrain_cluster_missing",
        "terrain_cluster_unknown", "terrain_subcluster_ok", "terrain_subcluster_mismatch", "terrain_dat_ok",
        "terrain_dat_missing", "mapload_ok", "mapload_missing", "mapload_no_id", "cluster_entry_ok",
        "cluster_entry_mismatch", "registration_ok", "registration_missing", "pack_ok", "pack_missing")


def node(kind, status, reason="", optional=False, children=()):
    n = chain_mod.ChainNode(kind, kind, status=status, reason=reason, optional=optional)
    n.children = list(children)
    return n


class Packs(unittest.TestCase):
    def test_the_game_s_packs_and_a_built_copy_s_over_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            rev = Path(tmp, "game", "Data", "PC", "190852")
            rev.mkdir(parents=True)
            (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "a\\one.txt", b"game's")]))
            (rev / "IA_Common.dat").write_bytes(make_edat([("file", "b\\two.xyz", b"script")]))
            (Path(tmp, "game") / "RUSE.exe").write_bytes(b"MZ")
            built = Path(tmp, "built")
            built.mkdir()
            (built / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "a\\one.txt", b"built")]))
            with missionsteps.PackStore(Path(tmp, "game")) as game:
                self.assertEqual(game.get_raw("gameplay", "A/ONE.TXT"), b"game's")  # either slash, any case
                self.assertEqual(game.entry_paths("scripts", ".xyz"), ["b\\two.xyz"])
                self.assertEqual(game.entry_paths("maps"), [])  # a pack the game hasn't got: nothing in it
                self.assertIsNone(game.get_raw("gameplay", "a\\none.txt"))
                self.assertEqual(game.view("scripts").list(), ["b\\two.xyz"])
                with self.assertRaises(KeyError):
                    game.view("scripts").get("nope")
            with missionsteps.PackStore(Path(tmp, "game"), built) as both:
                self.assertEqual(both.get_raw("gameplay", "a\\one.txt"), b"built")  # the built copy's first
                self.assertEqual(both.read_many("scripts", ["b\\two.xyz", "x"]), {"b\\two.xyz": b"script"})


class Links(unittest.TestCase):
    def test_every_way_a_link_stands_has_words_in_every_language(self):
        for why in WHYS:
            with self.subTest(why=why):
                self.assertEqual(set(WORDS["mission_why_" + why]), LANGS)
        for state in ("ok", "missing", "mismatch", "optional", "unknown"):
            self.assertEqual(set(WORDS["mission_state_" + state]), LANGS)

    def test_links_worded(self):
        self.assertEqual(missionsteps._why(node("terrain-subcluster", chain_mod.MISMATCH)), "terrain_subcluster_mismatch")
        self.assertEqual(missionsteps._why(node("mapload", chain_mod.MISSING, "the slot has no GUID, so ...")),
                         "mapload_no_id")
        self.assertEqual(missionsteps._why(node("mapload", chain_mod.MISSING, "no TMapLoadInfo loads ...")),
                         "mapload_missing")
        self.assertEqual(missionsteps._why(node("dico", chain_mod.MISSING, optional=True)), "optional")

    def test_a_battle_map_needs_no_mission_script_or_texts_of_its_own(self):
        def walked(*_args):
            return node("scenario", chain_mod.OK, children=[
                node("scenario-file", chain_mod.OK),
                node("scenario-cluster", chain_mod.OK, children=[
                    node("script", chain_mod.MISSING, "no effetmap.xyz under ..."),
                    node("dico", chain_mod.MISSING, "no .dic for it in any language ..."),
                    node("terrain-cluster", chain_mod.MISSING, "no terrain clustermap at that path")])])
        with mock.patch.object(chain_mod, "walk", walked):
            battle = missionsteps.chain(None, "somewhere", "leveldesign.scenario", "mp")
            operation = missionsteps.chain(None, "somewhere", "leveldesign.scenario", "operation")
        self.assertEqual([(link["why"], link["depth"]) for link in battle["links"]],
                         [("scenario_file_ok", 0), ("scenario_cluster_ok", 0), ("optional", 1), ("optional", 1),
                          ("terrain_cluster_missing", 1)])
        self.assertEqual(battle["broken"], 1)        # only the ground: a battle map's script and texts aren't needed
        self.assertEqual(operation["broken"], 3)     # an Operation needs all three


class RealGame(unittest.TestCase):
    """Every shipped mission read through the Studio (only when the game and its index are here)."""

    def test_the_game_s_missions(self):
        from rusemod.steam import find_game
        found = find_game()
        if found is None:
            self.skipTest("R.U.S.E. isn't installed here")
        from rusemod.index import default_path
        if not Path(default_path(found["game_dir"])).is_file():
            self.skipTest("the game index isn't built here")
        from ruse_mod_engine import scenario_registry as SR
        from ruse_studio.api import StudioApi
        game = Path(found["game_dir"])
        with missionsteps.PackStore(game) as store:
            m_ndf, g_ndf = SR.open_registry(store.view("gameplay"))
            bound = SR.build_bindings(m_ndf, g_ndf, store.view("maps"), gd=store.view("gameplay"),
                                      ia=store.view("scripts"))
            seen = {}
            for map_dir, bs in bound.items():
                for b in bs:
                    if b.kind in missionsteps.KINDS and b.has_file:
                        seen[b.kind] = seen.get(b.kind, 0) + 1
                        ch = missionsteps.chain(store, map_dir, b.scenario_name, b.kind)
                        self.assertEqual(ch["broken"], 0, (map_dir, b.scenario_name))
                        self.assertTrue({link["why"] for link in ch["links"]} <= set(WHYS))
        self.assertEqual(seen, {"mp": 30, "operation": 14, "campaign": 24})
        api = StudioApi()
        first = next((d, b) for d, bs in bound.items() for b in bs if b.kind == "operation" and b.has_file)
        got = api.mission_steps(first[0].upper(), first[1].scenario_name + ".scenario", "us")
        self.assertTrue(got["menu"]["listed"])
        self.assertTrue(got["menu"]["address"].startswith("$/Misc/Globals/ChallengePackManager:"))
        self.assertEqual(sum(o["this"] for o in got["menu"]["order"]), 1)
        self.assertTrue(all(o["title"] for o in got["menu"]["order"]))
        self.assertTrue(got["texts"] and all(t["words"] is not None for t in got["texts"] if t["where"] == "menu"))


if __name__ == "__main__":
    unittest.main()
