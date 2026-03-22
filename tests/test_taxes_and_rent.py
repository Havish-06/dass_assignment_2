import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game
from moneypoly.config import INCOME_TAX_POSITION, LUXURY_TAX_POSITION, INCOME_TAX_AMOUNT, LUXURY_TAX_AMOUNT


class TaxesAndRentTests(unittest.TestCase):
    """White-box tests for tax tiles and rent bankruptcy behaviour."""

    def setUp(self):
        self.game = Game(["P1", "P2"])
        self.p1, self.p2 = self.game.players

    def _land_on(self, player, position):
        """Helper: set player to position-1 then move 1 step via _move_and_resolve."""
        # Board size is fixed at 40 squares.
        player.position = (position - 1) % 40
        self.game._move_and_resolve(player, 1)  # pylint: disable=protected-access

    def test_income_tax_reduces_balance_but_not_eliminate_when_affordable(self):
        """Landing on income tax should deduct the fixed amount and keep player in game if still solvent."""
        starting = self.p1.balance
        self._land_on(self.p1, INCOME_TAX_POSITION)

        self.assertEqual(self.p1.balance, starting - INCOME_TAX_AMOUNT)
        self.assertIn(self.p1, self.game.players)
        self.assertFalse(self.p1.is_eliminated)

    def test_income_tax_can_bankrupt_and_eliminate_player(self):
        """If a player cannot afford income tax, they should go bankrupt and be removed."""
        self.p1.balance = INCOME_TAX_AMOUNT - 10

        self._land_on(self.p1, INCOME_TAX_POSITION)

        self.assertLess(self.p1.balance, 0)
        self.assertNotIn(self.p1, self.game.players)

    def test_luxury_tax_can_bankrupt_and_eliminate_player(self):
        """Luxury tax should also be able to bankrupt and eliminate a player."""
        self.p1.balance = LUXURY_TAX_AMOUNT - 5

        self._land_on(self.p1, LUXURY_TAX_POSITION)

        self.assertLess(self.p1.balance, 0)
        self.assertNotIn(self.p1, self.game.players)


if __name__ == "__main__":
    unittest.main()
