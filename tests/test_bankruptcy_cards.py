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

    def test_birthday_skips_players_who_cannot_afford_gift(self):
        """Birthday card should not bankrupt other players.

        A player with exactly the birthday amount is treated as unable to pay,
        so their balance and participation in the game are unchanged.
        """
        birthday_value = 10
        self.p2.balance = birthday_value
        self.p3.balance = 0  # Not solvent, so will not participate.

        card = {"description": "Birthday", "action": "birthday", "value": birthday_value}

        apply_card(self.game, self.p1, card)

        # P2 kept their money and remains active; no bankruptcy from birthday.
        self.assertEqual(self.p2.balance, birthday_value)
        self.assertFalse(self.p2.is_bankrupt())
        self.assertIn(self.p2, self.game.players)
        self.assertFalse(self.p2.is_eliminated)

    def test_collect_from_all_can_bankrupt_and_eliminate_other_players(self):
        """collect_from_all takes money whether or not players can afford it.

        Both P2 (who can just afford the payment) and P3 (who cannot afford it
        at all) are charged, and any player who becomes bankrupt is eliminated
        from the game.
        """
        collect_value = 20
        self.p2.balance = collect_value
        self.p3.balance = 0

        card = {
            "description": "Collect from all",
            "action": "collect_from_all",
            "value": collect_value,
        }

        apply_card(self.game, self.p1, card)

        # P2 hits exactly 0 and is eliminated.
        self.assertEqual(self.p2.balance, 0)
        self.assertTrue(self.p2.is_bankrupt())
        self.assertNotIn(self.p2, self.game.players)
        self.assertTrue(self.p2.is_eliminated)

        # P3 goes negative and is also eliminated.
        self.assertLess(self.p3.balance, 0)
        self.assertTrue(self.p3.is_bankrupt())
        self.assertNotIn(self.p3, self.game.players)
        self.assertTrue(self.p3.is_eliminated)


if __name__ == "__main__":
    unittest.main()
