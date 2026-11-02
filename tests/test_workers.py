"""Every worker program the apps start starts fresh, on every system (rusemod.mend.fresh_workers): Linux's own way
starts a copy of the running program, which can hang when a thread held a lock at that moment and carries whatever was
swapped in then (Studio 0.9.8.10's checks on Linux, 2026-11-01: a test's stand-in went into KeptModels' workers)."""
import ast
import multiprocessing
import unittest
from pathlib import Path

from rusemod import mend

SRC = Path(__file__).resolve().parents[1] / "src"


class FreshWorkers(unittest.TestCase):
    def test_the_apps_way_is_a_fresh_program(self):
        self.assertEqual(mend.fresh_workers().get_start_method(), "spawn")
        self.assertIs(mend.fresh_workers(), multiprocessing.get_context("spawn"))

    def test_every_pool_says_how_its_workers_start(self):
        loose = []
        for path in sorted(SRC.rglob("*.py")):
            if "python251" in path.parts:
                continue  # Python 2.5.1's own library where a PC has unpacked it
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in (
                        "ProcessPoolExecutor", "Pool", "Process"):
                    if not any(k.arg in ("mp_context", "context") for k in node.keywords):
                        loose.append(f"{path.relative_to(SRC)}:{node.lineno}")
        self.assertEqual(loose, [], "worker programs started the system's own way: pass mp_context=fresh_workers()")


if __name__ == "__main__":
    unittest.main()
