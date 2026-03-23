import os
import sys
import pytest
from unittest import mock


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from moneypoly.game import Game, apply_card
import moneypoly.ui as ui_module
import main as main_module
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


class TestGameMenuAndAuction:
    """Tests covering Game menus, auctions, mortgage helpers, and card edge cases."""

    def setup_method(self):
        self.game = Game(["P1", "P2"])
        (self.p1, self.p2) = self.game.players
        self.original_safe_int = ui_module.safe_int_input
        self.original_confirm = ui_module.confirm

    def teardown_method(self):
        ui_module.safe_int_input = self.original_safe_int
        ui_module.confirm = self.original_confirm

    def test_apply_card_unknown_action_warns_and_does_nothing(self):
        """Unknown card actions should not crash and should not change players."""
        card = {"description": "Weird", "action": "unknown_action", "value": 0}
        before_players = list(self.game.players)
        apply_card(self.game, self.p1, card)
        assert self.game.players == before_players

    def test_mortgage_and_unmortgage_property_paths(self):
        board = self.game.board
        prop = board.properties[0]

        # Cannot mortgage property you do not own.
        assert not self.game.mortgage_property(self.p1, prop)

        # Successful mortgage when owned and not already mortgaged.
        prop.owner = self.p1
        self.p1.add_property(prop)
        start_balance = self.p1.balance
        assert self.game.mortgage_property(self.p1, prop)
        assert prop.is_mortgaged
        assert self.p1.balance == start_balance + prop.mortgage_value

        # Attempting to mortgage again should fail.
        assert not self.game.mortgage_property(self.p1, prop)

        # Unmortgage: not owner should fail.
        other = self.p2
        prop.owner = other
        assert not self.game.unmortgage_property(self.p1, prop)

        # Reset owner and ensure property is NOT mortgaged for initial checks.
        prop.owner = self.p1
        prop.is_mortgaged = False
        # Not mortgaged: unmortgage should report "not mortgaged" and fail.
        assert not self.game.unmortgage_property(self.p1, prop)

        # Now mortgage it for unmortgage tests.
        prop.is_mortgaged = True
        # Cannot afford unmortgage.
        self.p1.balance = 0
        assert not self.game.unmortgage_property(self.p1, prop)

        # Afford unmortgage.
        self.p1.balance = 10_000
        assert self.game.unmortgage_property(self.p1, prop)
        assert not prop.is_mortgaged

    def test_menu_mortgage_and_unmortgage_and_trade(self):
        """Drive _menu_mortgage/_menu_unmortgage/_menu_trade via safe_int_input stubs."""

        board = self.game.board
        prop = board.properties[0]
        prop.owner = self.p1
        self.p1.add_property(prop)

        # _menu_mortgage: first index 1 selects the only mortgageable property.
        calls = []

        def fake_safe_int_input(_prompt, default=0):  
            return 1

        ui_module.safe_int_input = fake_safe_int_input

        original_mortgage_property = self.game.mortgage_property

        def spy_mortgage(player, chosen):  
            calls.append("mortgage")
            return original_mortgage_property(player, chosen)

        self.game.mortgage_property = spy_mortgage
        self.game._menu_mortgage(self.p1)  # pylint: disable=protected-access
        assert "mortgage" in calls

        # _menu_unmortgage: ensure there is a mortgaged property.
        prop.is_mortgaged = True
        calls.clear()

        original_unmortgage = self.game.unmortgage_property

        def spy_unmortgage(player, chosen):  
            calls.append("unmortgage")
            return original_unmortgage(player, chosen)

        self.game.unmortgage_property = spy_unmortgage
        self.game._menu_unmortgage(self.p1)  # pylint: disable=protected-access
        assert "unmortgage" in calls

        # _menu_trade: seller p1 has a property and trades with p2.
        self.p1.properties = [prop]
        self.p2.balance = 500

        sequence = [1, 1, 100]  # choose partner #1, property #1, $100 cash

        def trade_safe_int(_prompt, default=0):  
            return sequence.pop(0)

        ui_module.safe_int_input = trade_safe_int
        trade_calls = []

        def fake_trade(seller, buyer, chosen_prop, cash_amount):
            trade_calls.append((seller, buyer, chosen_prop, cash_amount))
            return True

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        assert len(trade_calls) == 1

    def test_menu_trade_returns_when_no_other_players(self):
        """_menu_trade should return early if there are no other players."""
        self.game.players = [self.p1]

        trade_calls = []

        def fake_trade(*_args, **_kwargs):
            trade_calls.append(1)

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        assert trade_calls == []

    def test_menu_trade_returns_when_player_has_no_properties(self):
        """_menu_trade should not call trade if the player has no properties."""
        board = self.game.board
        prop = board.properties[0]
        prop.owner = None
        self.p1.properties = []

        sequence = [1]  # choose partner #1 (valid)

        def safe_int(_prompt, default=0):
            return sequence.pop(0)

        ui_module.safe_int_input = safe_int
        trade_calls = []

        def fake_trade(*_args, **_kwargs):
            trade_calls.append(1)

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        assert trade_calls == []

    def test_menu_trade_returns_on_invalid_partner_selection(self):
        """Invalid partner index should cause _menu_trade to return without trading."""
        board = self.game.board
        prop = board.properties[0]
        prop.owner = self.p1
        self.p1.properties = [prop]

        def safe_int(_prompt, default=0):
            return 0  # results in idx = -1, which is invalid

        ui_module.safe_int_input = safe_int
        trade_calls = []

        def fake_trade(*_args, **_kwargs):
            trade_calls.append(1)

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        assert trade_calls == []

    def test_menu_trade_returns_on_invalid_property_selection(self):
        """Invalid property index should cause _menu_trade to return without trading."""
        board = self.game.board
        prop = board.properties[0]
        prop.owner = self.p1
        self.p1.properties = [prop]

        sequence = [1, 0]  # valid partner (idx 0), invalid property (pidx = -1)

        def safe_int(_prompt, default=0):
            return sequence.pop(0)

        ui_module.safe_int_input = safe_int
        trade_calls = []

        def fake_trade(*_args, **_kwargs):
            trade_calls.append(1)

        self.game.trade = fake_trade
        self.game._menu_trade(self.p1)  # pylint: disable=protected-access
        assert trade_calls == []

    def test_auction_property_no_bids_and_with_winner(self):
        board = self.game.board
        prop = board.properties[0]

        # First, auction with everyone passing (bid 0).
        bids = [0, 0]

        def safe_zero(_prompt, default=0):  
            return bids.pop(0)

        ui_module.safe_int_input = safe_zero
        self.game.auction_property(prop)
        assert prop.owner is None

        # Now, single player bids successfully.
        self.game.players = [self.p1]
        self.p1.balance = 500

        def safe_bid(_prompt, default=0):  
            return 200

        ui_module.safe_int_input = safe_bid
        self.game.auction_property(prop)
        assert prop.owner is self.p1

    def test_auction_property_rejects_low_and_unaffordable_bids(self):
        board = self.game.board
        prop = board.properties[0]

        # First, test a valid opening bid followed by a too-low raise.
        # P1 bids 50, P2 attempts only a 5 increase when the minimum
        # increment is higher, so their bid should be rejected.
        self.p1.balance = 500
        self.p2.balance = 500
        bids = [50, 55]

        def safe_bids(_prompt, default=0):  
            return bids.pop(0)

        ui_module.safe_int_input = safe_bids
        self.game.auction_property(prop)
        assert prop.owner is self.p1

        # Reset ownership for the next scenario.
        prop.owner = None
        if prop in self.p1.properties:
            self.p1.remove_property(prop)

        # Now, a single player attempts a bid they cannot afford.
        self.game.players = [self.p1]
        self.p1.balance = 100

        def unaffordable_bid(_prompt, default=0):  
            return 200

        ui_module.safe_int_input = unaffordable_bid
        start_bank = self.game.bank.get_balance()
        self.game.auction_property(prop)
        assert prop.owner is None
        assert self.game.bank.get_balance() == start_bank

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

        assert self.p1.jail.in_jail

    def test_play_turn_doubles_gives_extra_turn_without_advancing_player(self):
        """A single doubles roll should grant an extra turn (no advance_turn)."""
        # Avoid interactive_menu prompting for input.
        self.game.interactive_menu = lambda: None
        self.game.current_index = 0
        player = self.game.current_player()

        class _StubDice:
            def __init__(self):
                self.doubles_streak = 1  # already one doubles

            def roll(self):
                return 4

            def describe(self):  
                return "stub 4"

            def is_doubles(self):  
                return True

        self.game.dice = _StubDice()

        # Spy on advance_turn to ensure it is not called.
        advanced = {"value": False}
        original_advance = self.game.advance_turn

        def fake_advance():  
            advanced["value"] = True

        try:
            self.game.advance_turn = fake_advance
            self.game.play_turn()
        finally:
            self.game.advance_turn = original_advance

        # Current player index should be unchanged and advance_turn not called.
        assert self.game.current_index == 0
        assert not advanced["value"]

    def test_play_turn_moves_player_and_advances_turn_for_non_doubles(self):
        """Non-double roll should move the player and advance the turn."""
        # Stub out interactive_menu to avoid input.
        self.game.interactive_menu = lambda: None
        self.game.current_index = 0
        player = self.game.current_player()
        player.position = 0

        # Use the real Dice object but stub _move_and_resolve so that
        # movement is driven solely by play_turn and Dice.roll.
        steps_seen = {"value": None}

        real_move_resolve = self.game._move_and_resolve  # pylint: disable=protected-access

        def fake_move_resolve(p, steps):  
            steps_seen["value"] = steps
            # Still advance the player's position to keep semantics realistic.
            p.move(steps)

        try:
            self.game._move_and_resolve = fake_move_resolve  # pylint: disable=protected-access
            self.game.dice.die1 = 2
            self.game.dice.die2 = 3
            self.game.dice.doubles_streak = 0

            # Force a single non-double outcome.
            import moneypoly.dice as dice_module  # type: ignore

            original_randint = dice_module.random.randint

            rolls = [2, 3]

            def fake_randint(_low, _high):
                return rolls.pop(0)

            dice_module.random.randint = fake_randint

            try:
                self.game.play_turn()
            finally:
                dice_module.random.randint = original_randint
        finally:
            self.game._move_and_resolve = real_move_resolve  # pylint: disable=protected-access

        # Player should have moved by the rolled total and turn should advance.
        assert steps_seen["value"] == 5
        assert player.position == 5
        assert self.game.current_index == 1

    def test_play_turn_calls_jail_handler_for_jailed_player(self):
        """When the player starts in jail, play_turn should delegate to _handle_jail_turn."""
        self.p1.jail.in_jail = True
        self.game.current_index = 0

        handled = {"jail": False, "advanced": False}
        original_handle = self.game._handle_jail_turn  # pylint: disable=protected-access
        original_advance = self.game.advance_turn
        original_safe_int = ui_module.safe_int_input

        def fake_handle_jail(player):  
            handled["jail"] = True
            assert player is self.p1

        def fake_advance():  
            handled["advanced"] = True

        try:
            ui_module.safe_int_input = lambda _prompt, default=0: 0
            self.game._handle_jail_turn = fake_handle_jail  # pylint: disable=protected-access
            self.game.advance_turn = fake_advance
            self.game.play_turn()
        finally:
            self.game._handle_jail_turn = original_handle  # pylint: disable=protected-access
            self.game.advance_turn = original_advance
            ui_module.safe_int_input = original_safe_int

        assert handled["jail"]
        assert handled["advanced"]


class TestInteractiveMenu:
    """Directly exercise each interactive_menu choice branch with stubs."""

    def setup_method(self):
        self.game = Game(["P1", "P2"])
        self.original_safe_int = ui_module.safe_int_input
        self.original_print_standings = ui_module.print_standings
        self.original_print_board_ownership = ui_module.print_board_ownership

    def teardown_method(self):
        ui_module.safe_int_input = self.original_safe_int
        ui_module.print_standings = self.original_print_standings
        ui_module.print_board_ownership = self.original_print_board_ownership

    def test_interactive_menu_standings_and_exit(self):
        calls = []

        def fake_standings(players):  
            calls.append("standings")

        ui_module.print_standings = fake_standings
        sequence = [1, 0]

        def safe_sequence(_prompt, default=0):  
            return sequence.pop(0)

        ui_module.safe_int_input = safe_sequence
        self.game.interactive_menu()
        assert "standings" in calls

    def test_interactive_menu_board_and_mortgage_unmortgage_trade_loan(self):
        calls = []

        def fake_board(board):  
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

        def safe_menu(prompt, default=0):  
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
        assert "board" in calls
        assert "mortgage" in calls
        assert "unmortgage" in calls
        assert "trade" in calls
        assert "loan" in calls


class TestUI:
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
        # Also add a mortgaged property to exercise that branch.
        second_prop = board.properties[1]
        second_prop.owner = player
        second_prop.is_mortgaged = True
        player.add_property(second_prop)

        # Just ensure these functions execute without raising.
        ui_module.print_banner("Title")
        ui_module.print_player_card(player)
        ui_module.print_standings([player])
        ui_module.print_board_ownership(board)

        assert ui_module.format_currency(1500) == "$1,500"

    def test_safe_int_input_and_confirm(self):
        # safe_int_input returns an int when input is valid.
        with mock.patch("builtins.input", return_value="42"):
            assert ui_module.safe_int_input("x", default=0) == 42

        # safe_int_input falls back to default on invalid input.
        with mock.patch("builtins.input", return_value="not-an-int"):
            assert ui_module.safe_int_input("x", default=7) == 7

        # confirm interprets 'y' as True and anything else as False.
        with mock.patch("builtins.input", return_value="y"):
            assert ui_module.confirm("?")
        with mock.patch("builtins.input", return_value="n"):
            assert not ui_module.confirm("?")


class TestMainModule:
    """Tests for the main module entry point and its exception branches."""

    def test_main_normal_flow_uses_game(self):
        # Also exercise get_player_names itself by patching input.
        with mock.patch("builtins.input", return_value="A, B"):
            names = main_module.get_player_names()
        assert names == ["A", "B"]

        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            class DummyGame:
                def __init__(self, names):  
                    self.ran = False

                def run(self):
                    self.ran = True

            with mock.patch.object(main_module, "Game", DummyGame):
                main_module.main()

    def test_main_catches_keyboard_interrupt(self):
        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            def raising_init(_names):  
                raise KeyboardInterrupt()

            with mock.patch.object(main_module, "Game", side_effect=raising_init):
                main_module.main()  # should not raise

    def test_main_catches_value_error(self):
        with mock.patch.object(main_module, "get_player_names", return_value=["A", "B"]):

            def raising_init(_names):  
                raise ValueError("bad setup")

            with mock.patch.object(main_module, "Game", side_effect=raising_init):
                main_module.main()  # should not raise


if __name__ == "__main__":
    unittest.main()
