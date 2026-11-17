"""H17 chart checks and action-availability regressions using native pytest."""

from itertools import product

import pytest

from blackjack_trainer.cards import Card, RANKS
from blackjack_trainer.hands import evaluate_hand
from blackjack_trainer.strategy import Action, basic_strategy

UPCARDS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "A")


def cards(*ranks):
    return tuple(Card(rank, "♠") for rank in ranks)


# Expected chart cells are independent of the implementation's branching.
HARD_ROWS = {
    4: "HHHHHHHHHH", 5: "HHHHHHHHHH", 6: "HHHHHHHHHH", 7: "HHHHHHHHHH",
    8: "HHHHHHHHHH", 9: "HDDDDHHHHH", 10: "DDDDDDDDHH", 11: "DDDDDDDDDD",
    12: "HHSSSHHHHH", 13: "SSSSSHHHHH", 14: "SSSSSHHHHH", 15: "SSSSSHHHHH",
    16: "SSSSSHHHHH", 17: "SSSSSSSSSS", 18: "SSSSSSSSSS", 19: "SSSSSSSSSS",
    20: "SSSSSSSSSS",
}
SOFT_ROWS = {
    "2": "HHHDDHHHHH", "3": "HHHDDHHHHH", "4": "HHDDDHHHHH",
    "5": "HHDDDHHHHH", "6": "HDDDDHHHHH", "7": "DDDDDSSHHH",
    "8": "SSSSDSSSSS", "9": "SSSSSSSSSS",
}
PAIR_ROWS = {
    "2": "PPPPPPHHHH", "3": "PPPPPPHHHH", "4": "HHHPPHHHHH",
    "5": "DDDDDDDDHH", "6": "PPPPPHHHHH", "7": "PPPPPPHHHH",
    "8": "PPPPPPPPPP", "9": "PPPPPSPPSS", "10": "SSSSSSSSSS",
    "A": "PPPPPPPPPP",
}


def chart_cases(rows):
    return [(key, up, action) for key, row in rows.items()
            for up, action in zip(UPCARDS, row)]


@pytest.mark.parametrize("total,up,expected", chart_cases(HARD_ROWS))
def test_hard_chart(total, up, expected):
    hand = next(cards(a, b) for a, b in product(RANKS, repeat=2)
                if evaluate_hand(cards(a, b)).total == total
                and not evaluate_hand(cards(a, b)).is_soft)
    assert basic_strategy(hand, Card(up, "♥"), can_split=False).value == expected


@pytest.mark.parametrize("other,up,expected", chart_cases(SOFT_ROWS))
def test_soft_chart(other, up, expected):
    assert basic_strategy(cards("A", other), Card(up, "♥")).value == expected


@pytest.mark.parametrize("rank,up,expected", chart_cases(PAIR_ROWS))
def test_pair_chart(rank, up, expected):
    assert basic_strategy(cards(rank, rank), Card(up, "♥")).value == expected


@pytest.mark.parametrize("ranks,up,expected", [
    (("5", "6"), "A", Action.HIT),
    (("5", "5"), "9", Action.HIT),
    (("A", "6"), "4", Action.HIT),
    (("A", "7"), "2", Action.STAND),
    (("A", "8"), "6", Action.STAND),
])
def test_double_fallbacks(ranks, up, expected):
    assert basic_strategy(cards(*ranks), Card(up, "♥"), can_double=False) is expected


@pytest.mark.parametrize("ranks,up,expected", [
    (("8", "8"), "10", Action.HIT),
    (("8", "8"), "6", Action.STAND),
    (("6", "6"), "2", Action.HIT),
    (("6", "6"), "4", Action.STAND),
    (("4", "4"), "6", Action.HIT),
    (("A", "A"), "6", Action.HIT),
])
def test_unavailable_split_uses_total_fallback(ranks, up, expected):
    assert basic_strategy(cards(*ranks), Card(up, "♥"), can_split=False) is expected


@pytest.mark.parametrize("ranks,up,expected", [
    (("2", "3", "6"), "6", Action.HIT),
    (("A", "2", "4"), "5", Action.HIT),
    (("A", "2", "5"), "6", Action.STAND),
    (("A", "6", "10"), "10", Action.STAND),
    (("3", "3", "3"), "6", Action.HIT),
])
def test_multicard_hands_never_double_or_split(ranks, up, expected):
    assert basic_strategy(cards(*ranks), Card(up, "♥")) is expected


@pytest.mark.parametrize("rank", ("A", "2", "6", "10"))
def test_split_aces_lock_overrides_other_actions(rank):
    assert basic_strategy(cards("A", rank), Card("6", "♥"),
                          split_aces_locked=True) is Action.STAND


@pytest.mark.parametrize("ranks", [("A", "K"), ("7", "7", "7"), ("A", "A", "9")])
def test_twenty_one_stands(ranks):
    assert basic_strategy(cards(*ranks), Card("A", "♥")) is Action.STAND


@pytest.mark.parametrize("ranks", [(), ("A",), ("K", "Q", "2"), ("A", "K", "Q", "2")])
def test_non_playable_hands_are_rejected(ranks):
    with pytest.raises(ValueError):
        basic_strategy(cards(*ranks), Card("6", "♥"))


@pytest.mark.parametrize("rank", ("10", "J", "Q", "K"))
def test_dealer_face_cards_have_same_effect(rank):
    for first, second in product(RANKS, repeat=2):
        hand = cards(first, second)
        assert basic_strategy(hand, Card(rank, "♥")) == basic_strategy(hand, Card("10", "♥"))


def test_mixed_ten_pair_stands():
    assert basic_strategy(cards("J", "K"), Card("6", "♥")) is Action.STAND


def test_card_suits_do_not_change_strategy():
    assert basic_strategy([Card("8", "♥"), Card("8", "♦")], Card("10", "♣")) is Action.SPLIT


def test_action_codes_and_labels():
    assert [(action.value, action.label) for action in Action] == [
        ("H", "Hit"), ("S", "Stand"), ("D", "Double"), ("P", "Split")]


def test_strategy_does_not_mutate_hand():
    hand = list(cards("A", "7"))
    before = hand.copy()
    basic_strategy(hand, Card("2", "♥"))
    assert hand == before


def test_unavailable_actions_are_never_returned():
    for first, second, up in product(RANKS, RANKS, UPCARDS):
        assert basic_strategy(cards(first, second), Card(up, "♥"),
                              can_double=False, can_split=False) in (Action.HIT, Action.STAND)
