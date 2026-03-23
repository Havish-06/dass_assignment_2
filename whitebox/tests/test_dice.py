import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly import dice as dice_module
from moneypoly.cards import CardDeck


class DiceTests(unittest.TestCase):
    """Branch-coverage tests for the Dice helper."""

    def test_reset_clears_values_and_streak(self):
        dice = dice_module.Dice()
        dice.die1 = 3
        dice.die2 = 4
        dice.doubles_streak = 2

        dice.reset()

        self.assertEqual(dice.die1, 0)
        self.assertEqual(dice.die2, 0)
        self.assertEqual(dice.doubles_streak, 0)

    def test_roll_updates_doubles_streak_and_describe(self):
        """Exercise both doubles and non-doubles branches in roll/describe."""
        original_randint = dice_module.random.randint
        rolls = [2, 2, 3, 4]  # first roll doubles, second not

        def fake_randint(_low, _high):
            return rolls.pop(0)

        try:
            dice_module.random.randint = fake_randint
            dice = dice_module.Dice()
            dice.reset()

            total1 = dice.roll()
            self.assertEqual(total1, 4)
            self.assertTrue(dice.is_doubles())
            self.assertEqual(dice.doubles_streak, 1)
            self.assertIn("(DOUBLES)", dice.describe())

            total2 = dice.roll()
            self.assertEqual(total2, 7)
            self.assertFalse(dice.is_doubles())
            self.assertEqual(dice.doubles_streak, 0)
            self.assertNotIn("(DOUBLES)", dice.describe())
            # __repr__ should include the dice faces.
            rep = repr(dice)
            self.assertIn("Dice(", rep)
        finally:
            dice_module.random.randint = original_randint


class CardDeckTests(unittest.TestCase):
    """Branch-coverage tests for CardDeck behaviour."""

    def test_empty_deck_draw_and_peek(self):
        deck = CardDeck([])
        self.assertIsNone(deck.draw())
        self.assertIsNone(deck.peek())
        self.assertEqual(deck.cards_remaining(), 0)
        # __repr__ should work for an empty deck too.
        self.assertIn("CardDeck", repr(deck))
        self.assertEqual(len(deck), 0)

    def test_draw_cycles_through_cards_and_cards_remaining(self):
        cards = [
            {"description": "A", "action": "collect", "value": 10},
            {"description": "B", "action": "pay", "value": 5},
        ]
        deck = CardDeck(cards)

        first = deck.draw()
        second = deck.draw()
        third = deck.draw()  # triggers automatic reshuffle before drawing again

        self.assertEqual(first["description"], "A")
        self.assertEqual(second["description"], "B")
        # After reshuffle, the deck is still a permutation of the same cards,
        # so the third draw must be either "A" or "B".
        self.assertIn(third["description"], {"A", "B"})

        # Peek on a non-empty deck should return a card without advancing.
        current_index = deck.index
        next_card = deck.peek()
        self.assertIsNotNone(next_card)
        self.assertEqual(deck.index, current_index)

        # After three draws from a two-card deck and an automatic reshuffle,
        # the index should now point just past the first card again and there
        # should be exactly one card remaining before the next reshuffle.
        self.assertEqual(deck.cards_remaining(), 1)

    def test_auto_reshuffle_when_deck_exhausted(self):
        """Drawing past the end of the deck should reshuffle and restart."""
        import moneypoly.cards as cards_module  # type: ignore

        cards = [
            {"description": "A", "action": "collect", "value": 10},
            {"description": "B", "action": "pay", "value": 5},
            {"description": "C", "action": "collect", "value": 15},
        ]

        real_shuffle = cards_module.random.shuffle
        shuffle_calls = []

        def fake_shuffle(seq):
            # Record decks we reshuffle to observe order changes.
            shuffle_calls.append(list(seq))

        try:
            cards_module.random.shuffle = fake_shuffle
            deck = CardDeck(cards)

            # Draw all cards once.
            seen = [deck.draw()["description"] for _ in range(3)]
            self.assertCountEqual(seen, ["A", "B", "C"])

            # Next draw should trigger an automatic reshuffle before drawing
            # again, so shuffle must have been called at least once.
            next_card = deck.draw()
            self.assertIsNotNone(next_card)
            self.assertTrue(shuffle_calls)

            # After reshuffle, index should have advanced from 0 to 1 and
            # cards_remaining should report len(cards) - 1.
            self.assertEqual(deck.cards_remaining(), len(cards) - 1)
        finally:
            cards_module.random.shuffle = real_shuffle

    def test_reshuffle_resets_index(self):
        import moneypoly.cards as cards_module  # type: ignore

        real_shuffle = cards_module.random.shuffle
        calls = []

        def fake_shuffle(seq):
            # Record that we were called but otherwise leave order alone.
            calls.append(list(seq))

        try:
            cards_module.random.shuffle = fake_shuffle
            deck = CardDeck([
                {"description": "X", "action": "collect", "value": 5},
                {"description": "Y", "action": "pay", "value": 5},
            ])

            # Advance the index, then reshuffle which should reset it.
            _ = deck.draw()
            self.assertEqual(deck.index, 1)
            deck.reshuffle()
            self.assertEqual(deck.index, 0)
            self.assertTrue(calls)  # ensure shuffle was invoked
        finally:
            cards_module.random.shuffle = real_shuffle

    def test_len_and_repr_do_not_crash(self):
        cards = [
            {"description": "Z", "action": "collect", "value": 5},
        ]
        deck = CardDeck(cards)
        self.assertEqual(len(deck), 1)
        # __repr__ should return a non-empty string and not raise.
        rep = repr(deck)
        self.assertIsInstance(rep, str)
        self.assertIn("CardDeck", rep)


if __name__ == "__main__":
    unittest.main()
