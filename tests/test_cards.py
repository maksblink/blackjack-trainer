"""Tests for card validation and a standard deck."""

from dataclasses import FrozenInstanceError
import unittest

from blackjack_trainer.cards import Card, RANKS, SUITS, create_deck


class CardTests(unittest.TestCase):
    def test_card_representation(self):
        self.assertEqual(str(Card("A", "♠")), "A♠")
        self.assertEqual(str(Card("10", "♥")), "10♥")

    def test_equal_cards_are_hashable(self):
        self.assertEqual(len({Card("A", "♠"), Card("A", "♠")}), 1)
        self.assertNotEqual(Card("A", "♠"), Card("A", "♥"))

    def test_card_is_immutable(self):
        card = Card("A", "♠")
        with self.assertRaises(FrozenInstanceError):
            card.rank = "K"

    def test_invalid_rank_or_suit(self):
        for rank, suit in [("1", "♠"), ("a", "♠"), ("A", "spades"), ("", "")]:
            with self.subTest(rank=rank, suit=suit), self.assertRaises(ValueError):
                Card(rank, suit)

    def test_deck_contains_every_rank_suit_pair_once(self):
        deck = create_deck()
        self.assertEqual(len(deck), 52)
        self.assertEqual(set(deck), {Card(rank, suit) for rank in RANKS for suit in SUITS})

    def test_decks_are_independent_lists(self):
        first = create_deck()
        second = create_deck()
        first.pop()
        self.assertEqual(len(second), 52)


if __name__ == "__main__":
    unittest.main()
