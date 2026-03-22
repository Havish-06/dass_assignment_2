import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game, apply_card


class BirthdayAndCollectFromAllBankruptcyTests(unittest.TestCase):
    """Tests for birthday/collect_from_all cards and bankruptcy handling."""

    def setUp(self):
        # Simple 3-player game to exercise card effects.
        self.game = Game(["P1", "P2", "P3"])
        self.p1, self.p2, self.p3 = self.game.players

    def test_birthday_eliminates_other_player_when_they_go_bankrupt(self):
        """Birthday card should eliminate another player that hits balance 0."""
        # Arrange: P2 is just at the threshold of the birthday payment.
        birthday_value = 10
        self.p2.balance = birthday_value
        self.p3.balance = 0  # Not solvent, so will not participate.

        card = {"description": "Birthday", "action": "birthday", "value": birthday_value}

        # Act: apply the birthday card to P1.
        apply_card(self.game, self.p1, card)

        # Assert: P2 is bankrupt and has been removed from the game.
        self.assertEqual(self.p2.balance, 0)
        self.assertTrue(self.p2.is_bankrupt())
        self.assertNotIn(self.p2, self.game.players)
        self.assertTrue(self.p2.is_eliminated)

    def test_collect_from_all_eliminates_other_player_when_they_go_bankrupt(self):
        """collect_from_all should also eliminate any player that reaches 0."""
        collect_value = 20
        self.p2.balance = collect_value
        self.p3.balance = 0

        card = {
            "description": "Collect from all",
            "action": "collect_from_all",
            "value": collect_value,
        }

        apply_card(self.game, self.p1, card)

        self.assertEqual(self.p2.balance, 0)
        self.assertTrue(self.p2.is_bankrupt())
        self.assertNotIn(self.p2, self.game.players)
        self.assertTrue(self.p2.is_eliminated)


if __name__ == "__main__":
    unittest.main()
