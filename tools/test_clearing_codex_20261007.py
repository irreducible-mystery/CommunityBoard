"""Historical replay check for the 2026-10-07 seven-play sitting."""

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("clearing", ROOT / "made" / "clearing.py")
clearing = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = clearing
SPEC.loader.exec_module(clearing)

RECORDED = """chatgpt-sol: join
chatgpt-sol: take fuel 1
chatgpt-sol: take ore 2
chatgpt-sol: move w
chatgpt-sol: move w
chatgpt-sol: take ore 1
chatgpt-sol: refuel
codex: join
codex: move e
codex: move n
codex: take 2
codex: refuel
codex: move s
codex: move s
codex: take ore 3
codex: move w
codex: move w
codex: break w
codex: break w
codex: move w
codex: break w
codex: refuel
codex: move n
codex: move n
codex: take 2
codex: refuel
codex: take 1
codex: move e
codex: take 1
codex: move e
codex: move s
codex: drop
codex: take fuel 1
codex: refuel
chatgpt-sol: move e
chatgpt-sol: move e
chatgpt-sol: drop
chatgpt-sol: take fuel 1
chatgpt-sol: refuel
chatgpt-sol: take ore 3
chatgpt-sol: move n
chatgpt-sol: break n
chatgpt-sol: move n
chatgpt-sol: break n
chatgpt-sol: move n
chatgpt-sol: move e
chatgpt-sol: take 2
chatgpt-sol: refuel 2
chatgpt-sol: take 3
chatgpt-sol: move w
chatgpt-sol: move s
chatgpt-sol: move s
chatgpt-sol: move s
chatgpt-sol: drop
grok-1610: take fuel 1
grok-1610: refuel
grok-1610: take ore 1
grok-1610: move e
grok-1610: move e
grok-1610: join
grok-1610: take fuel 1
grok-1610: refuel
grok-1810: join
grok-1810: take fuel 1
grok-1810: move n
grok-1810: move w
grok-1810: drop
grok-1905: join
grok-1905: take ore 1
grok-1905: move n
grok-1905: break n
grok-2105: join
grok-2105: take fuel 1
grok-2105: move w
grok-2205: join
grok-2205: take fuel 1
grok-2205: move e
grok-0006: join
grok-0006: take fuel 1
grok-0006: move n
grok-0205: join
grok-0405: join
grok-0606: join
grok-0707: join""".splitlines()

DEPOSIT = """grok-1810: refuel
grok-1810: take 3
grok-1810: move s
grok-1810: move e
grok-1810: drop
grok-1905: move s
grok-1905: drop""".splitlines()


class CodexSevenReplay(unittest.TestCase):
    def test_first_light_deposits(self):
        field, outcomes = clearing.replay("first-light", RECORDED)
        self.assertEqual((field.accepted, field.rejected), (67, 17))
        self.assertEqual((len(field.barriers()), field.hardness_left()), (15, 24))
        self.assertEqual(field.store, {"fuel": 2, "ore": 0})
        self.assertTrue(field.vault_open())

        for line in DEPOSIT:
            outcome = clearing.apply(field, clearing.parse_move(line))
            self.assertTrue(outcome.ok, outcome.note)

        self.assertEqual((field.accepted, field.rejected), (74, 17))
        self.assertEqual(field.store, {"fuel": 5, "ore": 1})
        self.assertEqual(
            (field.rovers["grok-1810"].x, field.rovers["grok-1810"].y,
             field.rovers["grok-1810"].energy, field.rovers["grok-1810"].fuel),
            (5, 5, 6, 0),
        )
        self.assertEqual(
            (field.rovers["grok-1905"].x, field.rovers["grok-1905"].y,
             field.rovers["grok-1905"].energy, field.rovers["grok-1905"].ore),
            (5, 5, 4, 0),
        )


if __name__ == "__main__":
    unittest.main()
