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

    def test_find_winner_with_no_players_returns_none(self):
        """find_winner should return None cleanly when there are no players."""
        empty_game = Game([])

        winner = empty_game.find_winner()

        self.assertIsNone(winner)

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

    def test_move_lands_exactly_on_go_awards_salary(self):
        """Landing exactly on Go should also award the Go salary once."""
        self.a.position = BOARD_SIZE - 1
        starting_balance = self.a.balance

        new_pos = self.a.move(1)

        self.assertEqual(new_pos, 0)
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

    def test_buy_property_fails_when_balance_below_price(self):
        """A player with balance below the price should not be able to buy."""
        prop = self.game.board.properties[0]
        price = prop.price

        self.a.balance = price - 1

        success = self.game.buy_property(self.a, prop)

        self.assertFalse(success)
        self.assertIsNone(prop.owner)
        self.assertNotIn(prop, self.a.properties)

    def test_handle_property_tile_skip_with_s_leaves_property_unowned(self):
        """Choosing 's' to skip an unowned property should not buy or auction it."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.properties[0]
        prop.owner = None

        called = {"buy": False, "auction": False}

        original_buy = game.buy_property
        original_auction = game.auction_property

        def fake_buy(p, pr):  
            called["buy"] = True
            return original_buy(p, pr)

        def fake_auction(pr):  
            called["auction"] = True
            return original_auction(pr)

        game.buy_property = fake_buy
        game.auction_property = fake_auction

        # Simulate the player choosing to skip explicitly with 's'.
        import builtins  # type: ignore

        original_input = builtins.input
        try:
            builtins.input = lambda _prompt="": "s"
            game.handle_property_tile(player, prop)
        finally:
            builtins.input = original_input
            game.buy_property = original_buy
            game.auction_property = original_auction

        self.assertIsNone(prop.owner)
        self.assertFalse(called["buy"])
        self.assertFalse(called["auction"])

    def test_handle_property_tile_invalid_choice_loops_until_valid(self):
        """An invalid choice should loop and prompt again until a valid choice is made."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.properties[0]
        prop.owner = None

        called = {"buy": False, "auction": False}

        original_buy = game.buy_property
        original_auction = game.auction_property

        def fake_buy(p, pr):  
            called["buy"] = True
            return original_buy(p, pr)

        def fake_auction(pr):  
            called["auction"] = True
            return original_auction(pr)

        game.buy_property = fake_buy
        game.auction_property = fake_auction

        import builtins  # type: ignore

        original_input = builtins.input
        try:
            # Provide an invalid option 'x', then a valid 's'
            inputs = iter(["x", "s"])
            builtins.input = lambda _prompt="": next(inputs)
            game.handle_property_tile(player, prop)
        finally:
            builtins.input = original_input
            game.buy_property = original_buy
            game.auction_property = original_auction

        self.assertIsNone(prop.owner)
        self.assertFalse(called["buy"])
        self.assertFalse(called["auction"])



if __name__ == "__main__":
    unittest.main()
