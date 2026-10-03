"""A scripted scenario's camps (rusemod.missions), read from a mission script the way the game numbers them: a camp's
place in the launch descriptor's CampList, unless it sets its own CampNumber. The script below was compiled by the
game's own Python 2.5 from a made-up mission shaped like the game's (M03_Italie's first chapter lists its six camps in
the reverse of the order it makes them, and only the first is NiveauIA.Player):

    IR_10 = leveldesign.camps.VariableCamp(Alliance = 1, AllianceName = u'', CampNumber = -1, Couleur = ...,
                                           Nationalite = ...Nationalite.EU, NiveauIA = ...NiveauIA.Player, ...)
    IR_11 = ...VariableCamp(Alliance = 2, CampNumber = -1, Nationalite = ...Allemagne, NiveauIA = ...Scripted)
    IR_12 = ...VariableCamp(Alliance = 2, CampNumber = 9, Nationalite = ...Italie, NiveauIA = ...Scripted)
    def later(): IR_13 = ...VariableCamp(Alliance = 1, CampNumber = -1, Nationalite = ...RU)   (not in the list)
    IR_99 = launcheffetmap.DescriptorLaunchEffetMap(CampList = [IR_12, IR_11, IR_10], CampaignInfo = None)
"""
import hashlib
import struct
import unittest
import zlib

from rusemod import missions
from rusemod.pyscript import MAGIC, PY25, ScriptError

MARSHAL = bytes.fromhex(
    "630000000000000000110000004000000073fb0000006400006401006b00005a01006400006402006b01006c02005a020001"
    "650100690300690400640300640400640500640600640700640000640800650500690600690700640900650800690900690a"
    "00640a00650800690b00690c00640b00650d008300075a0e00650100690300690400640300640c0064070064000064090065"
    "0800690900690f00640a00650800690b006910008300045a1100650100690300690400640300640c00640700640d00640900"
    "650800690900691200640a00650800690b006910008300045a1300640e008400005a1400650200691500640f006513006511"
    "00650e006703006410006401008300025a170064010053281100000069ffffffff4e2801000000740e0000006c61756e6368"
    "65666665746d61707408000000416c6c69616e63656901000000740c000000416c6c69616e63654e616d657500000000740a"
    "00000043616d704e756d6265727407000000436f756c657572740b0000004e6174696f6e616c69746574080000004e697665"
    "61754941740d0000005061727461676543616d696f6e69020000006909000000630000000001000000070000004300000073"
    "2b0000007400006901006902006401006402006403006404006405007403006904006905008300037d00007c000053280600"
    "00004e52010000006901000000520300000069ffffffff52050000002806000000740b0000006c6576656c64657369676e74"
    "0500000063616d7073740c0000005661726961626c6543616d7074130000005f656e756d5f666f725f67616d655f706c6179"
    "5205000000740200000052552801000000740500000049525f313328000000002800000000730b00000065666665746d6170"
    "2e707974050000006c6174657207000000730400000000012701740800000043616d704c697374740c00000043616d706169"
    "676e496e666f281800000074110000006c6576656c64657369676e2e63616d7073520800000052000000005209000000520a"
    "0000007407000000646566696e65737406000000636f6c6f7273740e000000436f6c6f725f30375f477265656e520b000000"
    "52050000007402000000455552060000007406000000506c61796572740500000046616c7365740500000049525f31307409"
    "000000416c6c656d61676e6574080000005363726970746564740500000049525f313174060000004974616c696574050000"
    "0049525f3132520e000000741800000044657363726970746f724c61756e636845666665744d617074040000004e6f6e6574"
    "0500000049525f3939280000000028000000002800000000730b00000065666665746d61702e707973080000003c6d6f6475"
    "6c653e02000000730c0000000c0110014b01330133010903")


def xyz(marshal: bytes) -> bytes:
    """An .xyz file as the game stores one: XYZ0, Python 2.5's magic, the size, an MD5, the zlib'd marshal data."""
    return MAGIC + PY25 + struct.pack(">I", len(marshal)) + hashlib.md5(marshal).digest() + zlib.compress(marshal, 9)


class Camps(unittest.TestCase):
    def test_numbered_by_the_camp_list_or_their_own_number(self):
        got = missions.camps(xyz(MARSHAL))
        self.assertEqual([(c.key, c.var, c.player, c.ai, c.nation, c.alliance) for c in got], [
            (9, "IR_12", False, "Scripted", "Italie", 2),    # first in the list, but it sets CampNumber = 9
            (1, "IR_11", False, "Scripted", "Allemagne", 2),  # second in the list
            (2, "IR_10", True, "Player", "EU", 1)])           # third: the human player's camp
        self.assertEqual([missions.NATIONS[c.nation] for c in got], [4, 1, 0])

    def test_a_script_with_no_camp_list_has_no_camps(self):
        bare = MARSHAL.replace(b"CampList", b"CampLisX")  # the same script with the keyword renamed
        self.assertEqual(missions.camps(xyz(bare)), [])

    def test_not_a_script(self):
        with self.assertRaises(ScriptError):
            missions.camps(b"not a script at all")

    def test_where_a_scenarios_script_is(self):
        entries = ["genpython\\1000\\test\\map\\m03_italie\\scripting_chapter1\\effetmap.xyz",
                   "genpython\\1000\\test\\map\\m03_italie\\scripting\\effetmap.xyz", "other\\file.xyz"]
        self.assertEqual(missions.script_path(entries, "M03_Italie", "leveldesign_chapter1.scenario"), entries[0])
        self.assertEqual(missions.script_path(entries, "M03_Italie", "leveldesign.scenario"), entries[1])
        self.assertIsNone(missions.script_path(entries, "M03_Italie", "leveldesign_3v3_v01.scenario"))  # BATTLES


if __name__ == "__main__":
    unittest.main()
