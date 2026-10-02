"""The guard for the owner's hard rule (2026-10-02): never assume, never generalize. Every refusal about what R.U.S.E.
does is flagged with its rule, and every rule says what it rests on (rusemod.rules). It changes nothing the apps do."""
import ast
import re
import unittest
from pathlib import Path

from rusemod import rules

SRC = Path(__file__).resolve().parents[1] / "src"
# ruse_mod_engine is LittleGroove's engine as he wrote it (PLAN decision 26), not ours to tag; python251 is CPython's
SKIP = ("ruse_mod_engine", "python251")
# words that say what the game does (or that a player meets in it)
GAME = re.compile(r"\bgame\b|\bcrash|R\.U\.S\.E\.|\bmatch\b|\bplayers?\b|\bskirmish\b", re.I)
TAG = re.compile(r"#\s*(?:rule:\s*([a-z0-9-]+)|not a game rule\b)")


def _texts(node) -> str:
    return " ".join(n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str))


def _refusals(tree):
    """Every refusal in a module: raise X(...), Finding("error", ...), _find("error", ...), ("error", ...)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            yield node
        elif isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in ("Finding", "_find") \
                and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "error":
            yield node
        elif isinstance(node, ast.Tuple) and node.elts and isinstance(node.elts[0], ast.Constant) \
                and node.elts[0].value == "error":
            yield node


def _modules():
    for p in sorted(SRC.rglob("*.py")):
        if not any(part in SKIP for part in p.parts):
            yield p, p.read_text(encoding="utf-8")


class Guard(unittest.TestCase):
    def test_every_refusal_about_the_game_is_flagged(self):
        untagged, unknown = [], []
        for path, text in _modules():
            lines = text.splitlines()
            for node in _refusals(ast.parse(text)):
                if not GAME.search(_texts(node)):
                    continue
                span = "\n".join(lines[max(0, node.lineno - 2):node.end_lineno])
                where = f"{path.relative_to(SRC)}:{node.lineno}"
                if not TAG.search(span):
                    untagged.append(where)
                unknown += [f"{where} {r}" for r in TAG.findall(span) if r and r not in rules.RULES]
        self.assertEqual(untagged, [], "a refusal about the game with neither '# rule: <id>' (rusemod.rules) nor "
                                       "'# not a game rule: <why>' on its line or the one before")
        self.assertEqual(unknown, [], "a '# rule:' id that isn't in rusemod.rules.RULES")

    def test_every_rule_says_what_it_rests_on(self):
        for rule_id, rule in rules.RULES.items():
            with self.subTest(rule_id):
                self.assertIn(rule.basis, rules.BASES)
                self.assertTrue(rule.evidence.strip(), "no evidence written down")
                self.assertEqual(rule.tested, rule.basis == "game")

    def test_every_rule_is_applied_somewhere(self):
        used = set()
        for _path, text in _modules():
            used |= {m for m in TAG.findall(text) if m}
        self.assertEqual(sorted(set(rules.RULES) - used), [], "a rule in rusemod.rules that no code applies")


if __name__ == "__main__":
    unittest.main()
