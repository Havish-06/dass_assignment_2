import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game, apply_card
from moneypoly import ui
from moneypoly.config import JAIL_FINE


class JailAndCardsTests(unittest.TestCase):
    """White-box tests for jail-turn branches and card edge cases."""

    def setUp(self):
        self.game = Game(["P1"])
        self.player = self.game.players[0]

    def _patch_for_jail(self, confirm_value):
        """Patch ui.confirm, dice, and _move_and_resolve for deterministic jail tests."""
        originals = {
            "confirm": ui.confirm,
            "roll": self.game.dice.roll,
            "describe": self.game.dice.describe,
            "move_resolve": self.game._move_and_resolve,  # pylint: disable=protected-access
        }

        def fake_confirm(prompt):  # pylint: disable=unused-argument
            return confirm_value

        ui.confirm = fake_confirm
        self.game.dice.roll = lambda: 1
        self.game.dice.describe = lambda: "1"
        called = {"value": False}

        def fake_move(player, steps):  # pylint: disable=unused-argument
            called["value"] = True

        self.game._move_and_resolve = fake_move  # pylint: disable=protected-access
        return originals, called

    def _restore_from_jail_patch(self, originals):
        ui.confirm = originals["confirm"]
        self.game.dice.roll = originals["roll"]
        self.game.dice.describe = originals["describe"]
        self.game._move_and_resolve = originals["move_resolve"]  # pylint: disable=protected-access

    def test_use_get_out_of_jail_free_card_with_confirm_yes(self):
        """Player with a jail card who confirms 'yes' uses the card and moves."""
        self.player.go_to_jail()
        self.player.jail.cards = 1

        originals, called = self._patch_for_jail(confirm_value=True)
        try:
            self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            self._restore_from_jail_patch(originals)

        self.assertFalse(self.player.jail.in_jail)
        self.assertEqual(self.player.jail.cards, 0)
        self.assertTrue(called["value"])

    def test_decline_all_options_increments_jail_turn_counter(self):
        """If player declines card and fine, only the jail turn counter advances."""
        self.player.go_to_jail()
        self.player.jail.cards = 0
        start_turns = self.player.jail.turns

        # First confirm: use card? (no, but no cards anyway)
        # Second confirm: pay fine? (no)
        original_confirm = ui.confirm

        class _StubDice:  # local stub to count rolls
            def __init__(self):
                self.roll_calls = 0

            def roll(self):
                self.roll_calls += 1
                return 0

            def describe(self):
                return "stub 0"

        stub_dice = _StubDice()
        original_dice = self.game.dice

        try:
            ui.confirm = lambda _prompt: False
            self.game.dice = stub_dice
            self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            ui.confirm = original_confirm
            self.game.dice = original_dice

        self.assertTrue(self.player.jail.in_jail)
        self.assertEqual(self.player.jail.turns, start_turns + 1)
        self.assertEqual(stub_dice.roll_calls, 0)

    def test_jail_turn_voluntary_fine_deducts_from_player(self):
        """Paying the jail fine voluntarily should charge the player and move them."""        
        self.player.go_to_jail()
        start_balance = self.player.balance
        start_bank = self.game.bank.get_balance()

        originals, called = self._patch_for_jail(confirm_value=True)
        # Ensure no jail card so the confirm applies to the fine.
        self.player.jail.cards = 0
        try:
            self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            self._restore_from_jail_patch(originals)

        self.assertFalse(self.player.jail.in_jail)
        self.assertEqual(self.player.balance, start_balance - JAIL_FINE)
        self.assertEqual(self.game.bank.get_balance(), start_bank + JAIL_FINE)
        self.assertTrue(called["value"])

    def test_jail_voluntary_fine_can_bankrupt_and_prevent_movement(self):
        """If paying the jail fine bankrupts the player, they should be eliminated and not move."""
        self.player.go_to_jail()
        # Set balance so that paying the fine uses up all remaining cash.
        self.player.balance = JAIL_FINE - 10
        start_balance = self.player.balance
        start_bank = self.game.bank.get_balance()
        originals, called = self._patch_for_jail(confirm_value=True)
        self.player.jail.cards = 0
        try:
            self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            self._restore_from_jail_patch(originals)

        # Player should have paid only what they had and then gone bankrupt.
        self.assertEqual(self.player.balance, 0)
        self.assertEqual(self.game.bank.get_balance(), start_bank + start_balance)
        self.assertTrue(self.player.is_bankrupt())
        self.assertTrue(self.player.is_eliminated)
        self.assertNotIn(self.player, self.game.players)
        # No move should be attempted once the player is bankrupt.
        self.assertFalse(called["value"])

    def test_jail_mandatory_fine_bankruptcy_only_collects_available_cash(self):
        """Mandatory fine after three turns should only transfer existing cash if bankrupt."""
        self.player.go_to_jail()
        # Low balance so the mandatory fine will bankrupt the player.
        self.player.balance = JAIL_FINE - 5
        start_balance = self.player.balance
        start_bank = self.game.bank.get_balance()

        originals, called = self._patch_for_jail(confirm_value=False)
        self.player.jail.cards = 0
        try:
            for _ in range(3):
                self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            self._restore_from_jail_patch(originals)

        self.assertEqual(self.player.balance, 0)
        self.assertEqual(self.game.bank.get_balance(), start_bank + start_balance)
        self.assertTrue(self.player.is_bankrupt())
        self.assertTrue(self.player.is_eliminated)
        self.assertNotIn(self.player, self.game.players)
        # Mandatory bankrupt release should not attempt movement.
        self.assertFalse(called["value"])

    def test_jail_turn_mandatory_fine_after_three_turns(self):
        """After three skipped turns, the player must pay the fine and leave jail."""
        self.player.go_to_jail()
        start_balance = self.player.balance
        start_bank = self.game.bank.get_balance()

        originals, called = self._patch_for_jail(confirm_value=False)
        self.player.jail.cards = 0
        try:
            # Three consecutive turns doing nothing.
            for _ in range(3):
                self.game._handle_jail_turn(self.player)  # pylint: disable=protected-access
        finally:
            self._restore_from_jail_patch(originals)

        self.assertFalse(self.player.jail.in_jail)
        self.assertEqual(self.player.balance, start_balance - JAIL_FINE)
        self.assertEqual(self.game.bank.get_balance(), start_bank + JAIL_FINE)
        self.assertTrue(called["value"])

    def test_unknown_card_action_does_not_change_balances(self):
        """An unknown card action should not crash or change balances."""
        # Add a second player so we can watch more than one balance.
        self.game = Game(["P1", "P2"])
        p1, p2 = self.game.players
        start_balances = (p1.balance, p2.balance)

        card = {"description": "Weird", "action": "not_a_real_action", "value": 999}
        apply_card(self.game, p1, card)

        self.assertEqual((p1.balance, p2.balance), start_balances)


if __name__ == "__main__":
    unittest.main()
