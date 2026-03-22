import os
import sys
import unittest
from unittest import mock


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game, apply_card
import moneypoly.ui as ui_module
import moneypoly.main as main_module
from moneypoly.board import Board
from moneypoly.player import Player


class _StubDiceForPlay:
    """Stub dice to control doubles behaviour in Game.play_turn tests."""

    def __init__(self, totals, doubles_flags):
        self._totals = list(totals)
        self._doubles_flags = list(doubles_flags)
        self.doubles_streak = 0

    def roll(self):
        total = self._totals.pop(0)
        is_double = self._doubles_flags.pop(0)
        if is_double:
            self.doubles_streak += 1
        else:
            self.doubles_streak = 0
        return total

    def is_doubles(self):
        # Last outcome is doubles iff the last flag we processed was True.
        return self.doubles_streak > 0

    def describe(self):
        return "stub"  # description not important for tests


class GameMenuAndAuctionTests(unittest.TestCase):
    """Tests covering Game menus, auctions, mortgage helpers, and card edge cases."""

    def setUp(self):
        self.game = Game(["P1", "P2"])
        (self.p1, self.p2) = self.game.players
        self.original_safe_int = ui_module.safe_int_input
        self.original_confirm = ui_module.confirm

    def tearDown(self):
        ui_module.safe_int_input = self.original_safe_int
        ui_module.confirm = self.original_confirm

    def test_apply_card_unknown_action_warns_and_does_nothing(self):
        """Unknown card actions should not crash and should not change players."""
        card = {"description": "Weird", "action": "unknown_action", "value": 0}
        before_players = list(self.game.players)
        apply_card(self.game, self.p1, card)
        self.assertEqual(self.game.players, before_players)

    def test_mortgage_and_unmortgage_property_paths(self):
        board = self.game.board
        prop = board.properties[0]

        # Cannot mortgage property you do not own.
        self.assertFalse(self.game.mortgage_property(self.p1, prop))

        # Successful mortgage when owned and not already mortgaged.
        prop.owner = self.p1
        self.p1.add_property(prop)
        start_balance = self.p1.balance
        self.assertTrue(self.game.mortgage_property(self.p1, prop))
        self.assertTrue(prop.is_mortgaged)
        self.assertEqual(self.p1.balance, start_balance + prop.mortgage_value)

        # Attempting to mortgage again should fail.
        self.assertFalse(self.game.mortgage_property(self.p1, prop))

        # Unmortgage: not owner should fail.
        other = self.p2
        prop.owner = other
        self.assertFalse(self.game.unmortgage_property(self.p1, prop))

        # Reset owner and ensure property is NOT mortgaged for initial checks.
        prop.owner = self.p1
        prop.is_mortgaged = False
        # Not mortgaged: unmortgage should report "not mortgaged" and fail.
        self.assertFalse(self.game.unmortgage_property(self.p1, prop))

        # Now mortgage it for unmortgage tests.
        prop.is_mortgaged = True
        # Cannot afford unmortgage.
        self.p1.balance = 0
        self.assertFalse(self.game.unmortgage_property(self.p1, prop))

        # Afford unmortgage.
        self.p1.balance = 10_000
        self.assertTrue(self.game.unmortgage_property(self.p1, prop))
        self.assertFalse(prop.is_mortgaged)

    def test_menu_mortgage_and_unmortgage_and_trade(self):
        """Drive _menu_mortgage/_menu_unmortgage/_menu_trade via safe_int_input stubs."""

        board = self.game.board
        prop = board.properties[0]
        prop.owner = self.p1
        self.p1.add_property(prop)

        # _menu_mortgage: first index 1 selects the only mortgageable property.
        calls = []

        def fake_safe_int_input(_prompt, default=0):  # pylint: disable=unused-argument
            return 1

        ui_module.safe_int_input = fake_safe_int_input

        original_mortgage_property = self.game.mortgage_property

        def spy_mortgage(player, chosen):  # pylint: disable=unused-argument
            calls.append("mortgage")
            return original_mortgage_property(player, chosen)

        self.game.mortgage_property = spy_mortgage
        self.game._menu_mortgage(self.p1)  # pylint: disable=protected-access
        self.assertIn("mortgage", calls)

        # _menu_unmortgage: ensure there is a mortgaged property.
        prop.is_mortgaged = True
        calls.clear()

        original_unmortgage = self.game.unmortgage_property

        def spy_unmortgage(player, chosen):  # pylint: disable=unused-argument
            calls.append("unmortgage")
            return original_unmortgage(player, chosen)

        self.game.unmortgage_property = spy_unmortgage
        self.game._menu_unmortgage(self.p1)  # pylint: disable=protected-access
        self.assertIn("unmortgage", calls)

        # _menu_trade: seller p1 has a property and trades with p2.
        self.p1.properties = [prop]
        self.p2.balance = 500

        sequence = [1, 1, 100]  # choose partner #1, property #1, $100 cash

        def trade_safe_int(_prompt, default=0):  # pylint: disable=unused-argument
            return sequence.pop(0)

        ui_module.safe_int_input = trade_safe_int
        trade_calls = []

        def fake_trade(seller, buyer, chosen_prop, cash_amount):
            trade_calls.append((seller, buyer, chosen_prop, cash_amount))
            return True

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        self.assertEqual(len(trade_calls), 1)

    def test_auction_property_no_bids_and_with_winner(self):
        board = self.game.board
        prop = board.properties[0]

        # First, auction with everyone passing (bid 0).
        bids = [0, 0]

        def safe_zero(_prompt, default=0):  # pylint: disable=unused-argument
            return bids.pop(0)

        ui_module.safe_int_input = safe_zero
        self.game.auction_property(prop)
        self.assertIsNone(prop.owner)

        # Now, single player bids successfully.
        self.game.players = [self.p1]
        self.p1.balance = 500

        def safe_bid(_prompt, default=0):  # pylint: disable=unused-argument
            return 200

        ui_module.safe_int_input = safe_bid
        self.game.auction_property(prop)
        self.assertIs(prop.owner, self.p1)

    def test_play_turn_triple_doubles_sends_to_jail(self):
        """After three consecutive doubles, play_turn should jail the player."""
        # Ensure player starts free.
        self.p1.jail.in_jail = False
        self.game.current_index = 0

        # Stub dice to produce three doubles in a row.
        self.game.dice = _StubDiceForPlay(
            totals=[4, 4, 4], doubles_flags=[True, True, True]
        )

        # Avoid interactive input when landing on an unowned property.
        with mock.patch("builtins.input", return_value="s"):
            # Call play_turn three times to build up the streak.
            self.game.play_turn()
            self.game.play_turn()
            self.game.play_turn()

        self.assertTrue(self.p1.jail.in_jail)


class InteractiveMenuTests(unittest.TestCase):
    """Directly exercise each interactive_menu choice branch with stubs."""

    def setUp(self):
        self.game = Game(["P1", "P2"])
        self.original_safe_int = ui_module.safe_int_input
        self.original_print_standings = ui_module.print_standings
        self.original_print_board_ownership = ui_module.print_board_ownership

    def tearDown(self):
        ui_module.safe_int_input = self.original_safe_int
        ui_module.print_standings = self.original_print_standings
        ui_module.print_board_ownership = self.original_print_board_ownership

    def test_interactive_menu_standings_and_exit(self):
        calls = []

        def fake_standings(players):  # pylint: disable=unused-argument
            calls.append("standings")

        ui_module.print_standings = fake_standings
        sequence = [1, 0]

        def safe_sequence(_prompt, default=0):  # pylint: disable=unused-argument
            return sequence.pop(0)

        ui_module.safe_int_input = safe_sequence
        self.game.interactive_menu()
        self.assertIn("standings", calls)

    def test_interactive_menu_board_and_mortgage_unmortgage_trade_loan(self):
        calls = []

        def fake_board(board):  # pylint: disable=unused-argument
            calls.append("board")

        ui_module.print_board_ownership = fake_board

        # Provide a simple property so mortgage/unmortgage menus have something to work with.
        board = self.game.board
        prop = board.properties[0]
        prop.owner = self.game.current_player()
        self.game.current_player().add_property(prop)

        # Sequence of choices: 2(board),3(mortgage),4(unmortgage),5(trade),6(loan),0(exit).
        choices = [2, 3, 4, 5, 6, 0]
        loan_amounts = [50]

        def safe_menu(prompt, default=0):  # pylint: disable=unused-argument
            if "Loan amount" in prompt:
                return loan_amounts.pop(0)
            return choices.pop(0)

        ui_module.safe_int_input = safe_menu

        # Spy on helpers to ensure they're invoked.
        self.game._menu_mortgage = lambda _p: calls.append("mortgage")  # pylint: disable=protected-access
        self.game._menu_unmortgage = lambda _p: calls.append("unmortgage")  # pylint: disable=protected-access
        self.game._menu_trade = lambda _p: calls.append("trade")  # pylint: disable=protected-access
        self.game.bank.give_loan = lambda _p, _a: calls.append("loan")

        self.game.interactive_menu()
        self.assertIn("board", calls)
        self.assertIn("mortgage", calls)
        self.assertIn("unmortgage", calls)
        self.assertIn("trade", calls)
        self.assertIn("loan", calls)


class UITests(unittest.TestCase):
    """White-box tests for ui helpers and input wrappers."""

    def test_print_helpers_and_format_currency(self):
        board = Board()
        player = Player("P1")

        # Give player some state to exercise branches in print_player_card.
        player.jail.in_jail = True
        player.jail.turns = 1
        player.jail.cards = 1
        first_prop = board.properties[0]
        first_prop.owner = player
        player.add_property(first_prop)

        # Just ensure these functions execute without raising.
        ui_module.print_banner("Title")
        ui_module.print_player_card(player)
        ui_module.print_standings([player])
        ui_module.print_board_ownership(board)

        self.assertEqual(ui_module.format_currency(1500), "$1,500")

    def test_safe_int_input_and_confirm(self):
        # safe_int_input returns an int when input is valid.
        with mock.patch("builtins.input", return_value="42"):
            self.assertEqual(ui_module.safe_int_input("x", default=0), 42)

        # safe_int_input falls back to default on invalid input.
        with mock.patch("builtins.input", return_value="not-an-int"):
            self.assertEqual(ui_module.safe_int_input("x", default=7), 7)

        # confirm interprets 'y' as True and anything else as False.
        with mock.patch("builtins.input", return_value="y"):
            self.assertTrue(ui_module.confirm("?"))
        with mock.patch("builtins.input", return_value="n"):
            self.assertFalse(ui_module.confirm("?"))


class MainModuleTests(unittest.TestCase):
    """Tests for the main module entry point and its exception branches."""

    def test_main_normal_flow_uses_game(self):
        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            class DummyGame:
                def __init__(self, names):  # pylint: disable=unused-argument
                    self.ran = False

                def run(self):
                    self.ran = True

            with mock.patch.object(main_module, "Game", DummyGame):
                main_module.main()

    def test_main_catches_keyboard_interrupt(self):
        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            def raising_init(_names):  # pylint: disable=unused-argument
                raise KeyboardInterrupt()

            with mock.patch.object(main_module, "Game", side_effect=raising_init):
                main_module.main()  # should not raise

    def test_main_catches_value_error(self):
        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            def raising_init(_names):  # pylint: disable=unused-argument
                raise ValueError("bad setup")

            with mock.patch.object(main_module, "Game", side_effect=raising_init):
                main_module.main()  # should not raise


if __name__ == "__main__":
    unittest.main()
