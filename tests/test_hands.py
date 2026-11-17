"""Tests for ace valuation, naturals, busts, and pair classification."""

from dataclasses import FrozenInstanceError
from itertools import product
import unittest

from blackjack_trainer.cards import Card, RANKS
from blackjack_trainer.hands import card_value, evaluate_hand, hand_value, is_soft, pair_rank


def cards(*ranks):
    return [Card(rank, "♠") for rank in ranks]


class HandTests(unittest.TestCase):
    def test_card_values(self):
        for rank in RANKS:
            expected = 11 if rank == "A" else 10 if rank in ("10", "J", "Q", "K") else int(rank)
            with self.subTest(rank=rank):
                self.assertEqual(card_value(Card(rank, "♠")), expected)

    def test_empty_hand(self):
        result = evaluate_hand([])
        self.assertEqual(result.total, 0)
        self.assertFalse(result.is_soft)
        self.assertFalse(result.is_blackjack)
        self.assertFalse(result.is_bust)
        self.assertIsNone(result.pair_rank)

    def test_hard_totals(self):
        for ranks, expected in [(('10', '6'), 16), (('2', '3', '4'), 9), (('K', 'Q'), 20)]:
            with self.subTest(ranks=ranks):
                result = evaluate_hand(cards(*ranks))
                self.assertEqual(result.total, expected)
                self.assertFalse(result.is_soft)

    def test_soft_hand_becomes_hard_after_hit(self):
        hand = cards('A', '6')
        self.assertEqual(hand_value(hand), 17)
        self.assertTrue(is_soft(hand))
        hand.append(Card('10', '♥'))
        self.assertEqual(hand_value(hand), 17)
        self.assertFalse(is_soft(hand))

    def test_multiple_aces(self):
        cases = [(('A', 'A'), 12, True), (('A', 'A', '9'), 21, True),
                 (('A', 'A', '9', 'K'), 21, False), (('A', 'A', 'A', '8'), 21, True),
                 (('A', 'A', 'A', '9'), 12, False)]
        for ranks, total, soft in cases:
            with self.subTest(ranks=ranks):
                result = evaluate_hand(cards(*ranks))
                self.assertEqual((result.total, result.is_soft), (total, soft))

    def test_all_ten_rank_naturals_in_both_orders(self):
        for rank in ('10', 'J', 'Q', 'K'):
            for ranks in [('A', rank), (rank, 'A')]:
                with self.subTest(ranks=ranks):
                    result = evaluate_hand(cards(*ranks))
                    self.assertEqual(result.total, 21)
                    self.assertTrue(result.is_blackjack)
                    self.assertTrue(result.is_soft)
                    self.assertFalse(result.is_bust)

    def test_three_card_21_is_not_blackjack(self):
        for ranks in [('7', '7', '7'), ('A', '5', '5'), ('A', 'A', '9')]:
            with self.subTest(ranks=ranks):
                result = evaluate_hand(cards(*ranks))
                self.assertEqual(result.total, 21)
                self.assertFalse(result.is_blackjack)

    def test_split_21_is_not_blackjack(self):
        result = evaluate_hand(cards('A', 'K'), from_split=True)
        self.assertEqual(result.total, 21)
        self.assertTrue(result.is_soft)
        self.assertFalse(result.is_blackjack)

    def test_bust_uses_lowest_ace_total(self):
        for ranks, total in [(('K', 'Q', '2'), 22), (('A', 'K', 'Q', '2'), 23),
                             (('A', 'A', 'K', 'Q'), 22)]:
            with self.subTest(ranks=ranks):
                result = evaluate_hand(cards(*ranks))
                self.assertEqual(result.total, total)
                self.assertTrue(result.is_bust)
                self.assertFalse(result.is_soft)
                self.assertFalse(result.is_blackjack)

    def test_pair_ranks(self):
        for rank in RANKS:
            expected = '10' if rank in ('10', 'J', 'Q', 'K') else rank
            with self.subTest(rank=rank):
                self.assertEqual(pair_rank([Card(rank, '♠'), Card(rank, '♥')]), expected)
                self.assertEqual(evaluate_hand(cards(rank, rank)).pair_rank, expected)

    def test_mixed_ten_rank_pairs(self):
        for first, second in product(('10', 'J', 'Q', 'K'), repeat=2):
            with self.subTest(first=first, second=second):
                self.assertEqual(pair_rank(cards(first, second)), '10')

    def test_non_pairs_and_wrong_hand_sizes(self):
        for ranks in [(), ('A',), ('2', '3'), ('A', 'K'), ('8', '8', '8')]:
            with self.subTest(ranks=ranks):
                self.assertIsNone(pair_rank(cards(*ranks)))

    def test_input_and_result_are_immutable_snapshots(self):
        hand = cards('A', '6')
        before = hand.copy()
        result = evaluate_hand(hand)
        self.assertEqual(hand, before)
        hand.append(Card('10', '♥'))
        self.assertEqual(result.total, 17)
        self.assertTrue(result.is_soft)
        with self.assertRaises(FrozenInstanceError):
            result.total = 0
        self.assertEqual(evaluate_hand(tuple(before)), result)

    def test_all_hands_up_to_three_cards_against_ace_assignment_oracle(self):
        # Independent oracle: enumerate all possible 1/11 assignments for aces.
        for size in range(4):
            for ranks in product(RANKS, repeat=size):
                values = [(1, 11) if rank == 'A' else
                          (10,) if rank in ('10', 'J', 'Q', 'K') else (int(rank),)
                          for rank in ranks]
                assignments = list(product(*values))
                totals = [sum(assignment) for assignment in assignments]
                non_busting = [total for total in totals if total <= 21]
                expected = max(non_busting) if non_busting else min(totals)
                expected_soft = any(sum(assignment) == expected and 11 in assignment
                                    for assignment in assignments)
                result = evaluate_hand(cards(*ranks))
                self.assertEqual(result.total, expected, ranks)
                self.assertEqual(result.is_soft, expected_soft, ranks)
                self.assertEqual(result.is_bust, expected > 21, ranks)


if __name__ == '__main__':
    unittest.main()
