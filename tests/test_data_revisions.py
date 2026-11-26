"""FL-121 (GitHub issue 25, 2026-11-15; the owner's "B18 A", 2026-11-26): leftover data revision folders in the game's
Data\\PC (a player's 1360 with a DataMap_Win.dat from 2016, 99, 64) made the build write a new map's scenario into 1360's
pack, which the game does not read (it reads 190852), so the map crashed on load. rusemod.steam.data_revisions sorted the
folder names as TEXT ("1360" before "190852", "99" last) while build.find_pack takes the first as the newest and
rusemod.index takes the last. Now: by number, oldest first; find_pack reads newest first; the troubleshooter warns
about the extra folders (it never changes the game's own folder)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import tempfile
import unittest
from pathlib import Path

from rusemod import doctor
from rusemod.build import find_pack
from rusemod.steam import data_revisions


def game_with(root: Path, revisions, pack_in) -> Path:
    game = root / "R.U.S.E"
    (game / "Data").mkdir(parents=True)
    (game / "RUSE.exe").write_bytes(b"exe")
    for rev in revisions:
        (game / "Data" / "PC" / rev).mkdir(parents=True)
    for rev in pack_in:
        (game / "Data" / "PC" / rev / "DataMap_Win.dat").write_bytes(b"pack")
    return game


class DataRevisionsByNumber(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_players_folders_sort_by_number_oldest_first(self):
        game = game_with(self.root, ["1360", "190852", "64", "99"], [])
        self.assertEqual(data_revisions(game), ["64", "99", "1360", "190852"])

    def test_find_pack_takes_the_newest_revision_the_game_reads(self):
        game = game_with(self.root, ["1360", "190852", "64", "99"], ["1360", "190852"])
        self.assertEqual(find_pack(game, "DataMap_Win.dat"), game / "Data" / "PC" / "190852" / "DataMap_Win.dat")

    def test_a_clean_install_is_as_before(self):
        game = game_with(self.root, ["190852"], ["190852"])
        self.assertEqual(data_revisions(game), ["190852"])
        self.assertEqual(find_pack(game, "DataMap_Win.dat"), game / "Data" / "PC" / "190852" / "DataMap_Win.dat")

    def test_the_troubleshooter_warns_about_extra_revision_folders(self):
        game = game_with(self.root, ["1360", "190852", "99"], ["1360", "190852"])
        found = [f for f in doctor.checks(game, None, steam_running=lambda: True, processes=[]) if f["key"] == "revisions"]
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0]["level"], found[0]["say"], found[0]["fix"]), ("warn", "doc_revisions_extra", None))
        self.assertEqual((found[0]["data"]["newest"], found[0]["data"]["extra"]), ("190852", "99, 1360"))

    def test_no_warning_for_a_clean_install(self):
        game = game_with(self.root, ["190852"], ["190852"])
        self.assertEqual([f for f in doctor.checks(game, None, steam_running=lambda: True, processes=[])
                          if f["key"] == "revisions"], [])


if __name__ == "__main__":
    unittest.main()
