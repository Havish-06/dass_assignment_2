import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game
from moneypoly.config import BOARD_SIZE, GO_SALARY


class WinnerMovementAndPurchaseTests(unittest.TestCase):
    """White-box tests for winner selection, movement, and property purchase."""

    def setUp(self):
        # Three players for comparing balances and ownership.
        self.game = Game(["A", "B", "C"])
        self.a, self.b, self.c = self.game.players

    def test_find_winner_picks_highest_net_worth(self):
        """Winner should be the player with the highest net worth (balance)."""
        self.a.balance = 100
        self.b.balance = 300
        self.c.balance = 50

        winner = self.game.find_winner()

        self.assertIsNotNone(winner)
        self.assertEqual(winner.name, "B")

    def test_move_past_go_awards_salary(self):
        """Moving past position 0 should award the Go salary once."""
        # Place player near the end of the board so a big move wraps around.
        self.a.position = BOARD_SIZE - 2
        starting_balance = self.a.balance

        # Move 4 steps: wraps from (BOARD_SIZE - 2) to (BOARD_SIZE + 2) % BOARD_SIZE == 2
        steps = 4
        new_pos = self.a.move(steps)

        self.assertEqual(new_pos, 2)
        # Player should have received exactly one Go salary.
        self.assertEqual(self.a.balance, starting_balance + GO_SALARY)

    def test_can_buy_property_with_exact_balance(self):
        """A player with balance equal to price should still be able to buy."""
        # Take the first property from the board for this test.
        prop = self.game.board.properties[0]
        price = prop.price

        self.a.balance = price

        success = self.game.buy_property(self.a, prop)

        self.assertTrue(success)
        self.assertIs(prop.owner, self.a)
        self.assertIn(prop, self.a.properties)
        # After purchase, balance should be zero.
        self.assertEqual(self.a.balance, 0)


if __name__ == "__main__":
    unittest.main()
