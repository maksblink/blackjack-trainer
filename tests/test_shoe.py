"""Tests for finite draws, composition, reproducibility and reshuffling."""

from collections import Counter
import random
import unittest

from blackjack_trainer.cards import create_deck
from blackjack_trainer.shoe import Shoe, ShoeExhaustedError


class ShoeTests(unittest.TestCase):
    def test_default_six_deck_composition(self):
        shoe = Shoe()
        self.assertEqual(shoe.number_of_decks, 6)
        self.assertEqual(shoe.remaining, 312)
        self.assertEqual(shoe.remaining_decks, 6.0)
        self.assertEqual(Counter(shoe.cards), Counter({card: 6 for card in create_deck()}))

    def test_custom_deck_count(self):
        self.assertEqual(Shoe(1).remaining, 52)
        self.assertEqual(Shoe(8).remaining, 416)

    def test_invalid_deck_count(self):
        for value in [0, -1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Shoe(value)
        for value in [True, 1.5, "6"]:
            with self.subTest(value=value), self.assertRaises(TypeError):
                Shoe(value)

    def test_draws_follow_order_and_advance_position(self):
        shoe = Shoe(1, shuffle=False)
        deck = create_deck()
        self.assertEqual(shoe.draw(), deck[0])
        self.assertEqual(shoe.draw_many(3), deck[1:4])
        self.assertEqual(shoe.position, 4)
        self.assertEqual(shoe.remaining, 48)
        self.assertAlmostEqual(shoe.remaining_decks, 48 / 52)

    def test_empty_draw_does_not_advance(self):
        shoe = Shoe(1)
        self.assertEqual(shoe.draw_many(0), [])
        self.assertEqual(shoe.position, 0)

    def test_invalid_draw_does_not_advance(self):
        shoe = Shoe(1)
        for value, error in [(-1, ValueError), (True, TypeError), (1.5, TypeError), ("2", TypeError)]:
            with self.subTest(value=value), self.assertRaises(error):
                shoe.draw_many(value)
            self.assertEqual(shoe.position, 0)

    def test_oversized_draw_is_atomic(self):
        shoe = Shoe(1, shuffle=False)
        shoe.draw_many(50)
        with self.assertRaises(ShoeExhaustedError):
            shoe.draw_many(3)
        self.assertEqual(shoe.position, 50)
        self.assertEqual(shoe.draw_many(2), create_deck()[-2:])

    def test_empty_shoe_does_not_automatically_reshuffle(self):
        shoe = Shoe(1)
        shoe.draw_many(52)
        with self.assertRaises(ShoeExhaustedError):
            shoe.draw()
        self.assertEqual(shoe.position, 52)
        self.assertEqual(shoe.remaining, 0)

    def test_complete_shoe_deals_exact_composition(self):
        shoe = Shoe(6)
        drawn = [shoe.draw() for _ in range(312)]
        self.assertEqual(Counter(drawn), Counter({card: 6 for card in create_deck()}))
        self.assertEqual(shoe.remaining, 0)

    def test_seeded_shuffle_is_reproducible(self):
        first = Shoe(rng=random.Random(42))
        second = Shoe(rng=random.Random(42))
        self.assertEqual(first.cards, second.cards)
        self.assertNotEqual(first.cards, Shoe(shuffle=False).cards)
        first.draw_many(10)
        first.shuffle()
        second.shuffle()
        self.assertEqual(first.cards, second.cards)

    def test_shuffle_restores_drawn_cards(self):
        shoe = Shoe(2, rng=random.Random(7))
        shoe.draw_many(60)
        shoe.shuffle()
        self.assertEqual(shoe.position, 0)
        self.assertEqual(shoe.remaining, 104)
        self.assertEqual(Counter(shoe.cards), Counter({card: 2 for card in create_deck()}))

    def test_returned_collections_cannot_modify_shoe(self):
        shoe = Shoe(1, shuffle=False)
        self.assertIsInstance(shoe.cards, tuple)
        drawn = shoe.draw_many(2)
        drawn.clear()
        self.assertEqual(shoe.remaining, 50)
        self.assertEqual(shoe.draw(), create_deck()[2])


if __name__ == "__main__":
    unittest.main()
