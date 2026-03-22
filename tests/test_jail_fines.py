import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game
from moneypoly.config import JAIL_FINE
import moneypoly.ui as ui_module


class _StubDice:
    """Simple stub dice to control rolls in jail tests."""

    def __init__(self, steps):
        self._steps = steps
        self.roll_calls = 0

    def roll(self):
        self.roll_calls += 1
        return self._steps

    def describe(self):
        return f"stub roll {self._steps}"


class JailFineTests(unittest.TestCase):
    """White-box tests for jail fine payment branches."""

    def setUp(self):
        self.game = Game(["P1", "P2"])
        self.p1, self.p2 = self.game.players
        self.original_confirm = ui_module.confirm

    def tearDown(self):
        ui_module.confirm = self.original_confirm

    def _send_to_jail(self, player):
        player.go_to_jail()
        self.assertTrue(player.jail.in_jail)

    def test_voluntary_fine_deducts_balance_and_checks_bankruptcy(self):
        """Paying the jail fine voluntarily should deduct from balance.

        When the player can afford the fine, they should be released and
        allowed to roll and move.
        """
        self._send_to_jail(self.p1)
        starting_balance = self.p1.balance

        ui_module.confirm = lambda prompt: True
        # Use a zero-step roll so we don't land on an owned or
        # purchasable property that would ask for interactive input.
        self.game.dice = _StubDice(steps=0)

        self.game._handle_jail_turn(self.p1)  # pylint: disable=protected-access

        self.assertEqual(self.p1.balance, starting_balance - JAIL_FINE)
        self.assertFalse(self.p1.jail.in_jail)
        self.assertEqual(self.game.dice.roll_calls, 1)

    def test_voluntary_fine_more_than_balance_eliminates_player_without_moving(self):
        """If fine exceeds balance, paying it should bankrupt and eliminate player.

        In this case the player should not get to roll or move after paying,
        because they are removed from the game immediately.
        """
        self._send_to_jail(self.p1)
        self.p1.balance = JAIL_FINE - 10

        ui_module.confirm = lambda prompt: True
        self.game.dice = _StubDice(steps=0)

        self.game._handle_jail_turn(self.p1)  # pylint: disable=protected-access

        self.assertNotIn(self.p1, self.game.players)
        self.assertTrue(self.p1.is_eliminated)
        self.assertEqual(self.game.dice.roll_calls, 0)


if __name__ == "__main__":
    unittest.main()
