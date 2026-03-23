import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly import dice as dice_module
from moneypoly.cards import CardDeck


class TestDice:
    """Branch-coverage tests for the Dice helper."""

    def test_reset_clears_values_and_streak(self):
        dice = dice_module.Dice()
        dice.die1 = 3
        dice.die2 = 4
        dice.doubles_streak = 2

        dice.reset()

        assert dice.die1 == 0
        assert dice.die2 == 0
        assert dice.doubles_streak == 0

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
            assert total1 == 4
            assert dice.is_doubles()
            assert dice.doubles_streak == 1
            assert "(DOUBLES)" in dice.describe()

            total2 = dice.roll()
            assert total2 == 7
            assert not dice.is_doubles()
            assert dice.doubles_streak == 0
            assert "(DOUBLES)" not in dice.describe()
            # __repr__ should include the dice faces.
            rep = repr(dice)
            assert "Dice(" in rep
        finally:
            dice_module.random.randint = original_randint


class TestCardDeck:
    """Branch-coverage tests for CardDeck behaviour."""

    def test_empty_deck_draw_and_peek(self):
        deck = CardDeck([])
        assert deck.draw() is None
        assert deck.peek() is None
        assert deck.cards_remaining() == 0
        # __repr__ should work for an empty deck too.
        assert "CardDeck" in repr(deck)
        assert len(deck) == 0

    def test_draw_cycles_through_cards_and_cards_remaining(self):
        cards = [
            {"description": "A", "action": "collect", "value": 10},
            {"description": "B", "action": "pay", "value": 5},
        ]
        deck = CardDeck(cards)

        first = deck.draw()
        second = deck.draw()
        third = deck.draw()  # triggers automatic reshuffle before drawing again

        assert first["description"] == "A"
        assert second["description"] == "B"
        # After reshuffle, the deck is still a permutation of the same cards,
        # so the third draw must be either "A" or "B".
        assert third["description"] in {"A", "B"}

        # Peek on a non-empty deck should return a card without advancing.
        current_index = deck.index
        next_card = deck.peek()
        assert next_card is not None
        assert deck.index == current_index

        # After three draws from a two-card deck and an automatic reshuffle,
        # the index should now point just past the first card again and there
        # should be exactly one card remaining before the next reshuffle.
        assert deck.cards_remaining() == 1

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
            assert sorted(seen) == sorted(["A", "B", "C"])

            # Next draw should trigger an automatic reshuffle before drawing
            # again, so shuffle must have been called at least once.
            next_card = deck.draw()
            assert next_card is not None
            assert shuffle_calls

            # After reshuffle, index should have advanced from 0 to 1 and
            # cards_remaining should report len(cards) - 1.
            assert deck.cards_remaining() == len(cards) - 1
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
            assert deck.index == 1
            deck.reshuffle()
            assert deck.index == 0
            assert calls
        finally:
            cards_module.random.shuffle = real_shuffle

    def test_len_and_repr_do_not_crash(self):
        cards = [
            {"description": "Z", "action": "collect", "value": 5},
        ]
        deck = CardDeck(cards)
        assert len(deck) == 1
        # __repr__ should return a non-empty string and not raise.
        rep = repr(deck)
        assert isinstance(rep, str)
        assert "CardDeck" in rep


if __name__ == "__main__":
    unittest.main()
