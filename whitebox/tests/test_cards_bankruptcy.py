import os
import sys
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game, apply_card
from moneypoly.config import GO_SALARY, JAIL_POSITION


class TestBirthdayAndCollectFromAllBankruptcy:
    """Tests for birthday/collect_from_all cards and bankruptcy handling."""

    def setup_method(self):
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
        assert self.p2.balance == birthday_value
        assert not self.p2.is_bankrupt()
        assert self.p2 in self.game.players
        assert not self.p2.is_eliminated

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
        assert self.p2.balance == 0
        assert self.p2.is_bankrupt()
        assert self.p2 not in self.game.players
        assert self.p2.is_eliminated

        # P3 goes negative and is also eliminated.
        assert self.p3.balance < 0
        assert self.p3.is_bankrupt()
        assert self.p3 not in self.game.players
        assert self.p3.is_eliminated

    def test_collect_card_pays_from_bank_to_player(self):
        """A 'collect' card should pay the player from the bank's funds."""
        self.game = Game(["P1"])
        (player,) = self.game.players
        start_player = player.balance
        start_bank = self.game.bank.get_balance()

        card = {"description": "Bank error in your favour", "action": "collect", "value": 50}

        apply_card(self.game, player, card)

        assert player.balance == start_player + 50
        assert self.game.bank.get_balance() == start_bank - 50

    def test_pay_card_charges_player_and_credits_bank(self):
        """A 'pay' card should deduct from the player and credit the bank."""
        self.game = Game(["P1"])
        (player,) = self.game.players
        start_player = player.balance
        start_bank = self.game.bank.get_balance()

        card = {"description": "Doctor's fees", "action": "pay", "value": 25}

        apply_card(self.game, player, card)

        assert player.balance == start_player - 25
        assert self.game.bank.get_balance() == start_bank + 25

    def test_jail_card_sends_player_directly_to_jail(self):
        """A 'jail' card should move the player directly to jail."""
        self.game = Game(["P1"])
        (player,) = self.game.players

        card = {"description": "Go to Jail", "action": "jail", "value": 0}

        apply_card(self.game, player, card)

        assert player.jail.in_jail
        assert player.position == JAIL_POSITION

    def test_jail_free_card_increases_jail_card_count(self):
        """A 'jail_free' card should grant a Get Out of Jail Free card."""
        self.game = Game(["P1"])
        (player,) = self.game.players
        assert player.jail.cards == 0

        card = {"description": "Get Out of Jail Free", "action": "jail_free", "value": 0}

        apply_card(self.game, player, card)

        assert player.jail.cards == 1

    def test_move_to_card_moves_player_and_awards_go_salary_when_passing(self):
        """A 'move_to' card should move the player and pay Go salary if passing Go."""
        self.game = Game(["P1"])
        (player,) = self.game.players
        # Start somewhere past Go so that moving back to 0 counts as passing.
        player.position = 10
        start_balance = player.balance

        card = {"description": "Advance to Go", "action": "move_to", "value": 0}

        apply_card(self.game, player, card)

        assert player.position == 0
        assert player.balance == start_balance + GO_SALARY

    def test_move_to_card_calls_handle_property_tile_when_landing_on_property(self):
        """A 'move_to' card should invoke property handling when landing on a property."""
        self.game = Game(["P1"])
        (player,) = self.game.players
        board = self.game.board
        target_prop = board.properties[0]
        player.position = 0

        calls = []

        def fake_handle_property_tile(passed_player, passed_prop):
            calls.append((passed_player, passed_prop))

        self.game.handle_property_tile = fake_handle_property_tile

        card = {
            "description": "Advance to a property",
            "action": "move_to",
            "value": target_prop.position,
        }

        apply_card(self.game, player, card)

        assert player.position == target_prop.position
        assert len(calls) == 1
        called_player, called_prop = calls[0]
        assert called_player is player
        assert called_prop is target_prop


if __name__ == "__main__":
    unittest.main()
