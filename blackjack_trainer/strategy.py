"""Total-dependent multi-deck H17/DAS basic strategy without surrender.

Assumes dealer peek, doubling on any first two cards, and double after split.
This is a fixed chart policy, not a remaining-shoe expected-value calculator.
"""

from collections.abc import Sequence
from enum import Enum

from blackjack_trainer.cards import Card
from blackjack_trainer.hands import card_value, evaluate_hand


class Action(str, Enum):
    HIT = "H"
    STAND = "S"
    DOUBLE = "D"
    SPLIT = "P"

    @property
    def label(self) -> str:
        return {Action.HIT: "Hit", Action.STAND: "Stand",
                Action.DOUBLE: "Double", Action.SPLIT: "Split"}[self]


def basic_strategy(
    player_hand: Sequence[Card],
    dealer_upcard: Card,
    *,
    can_double: bool = True,
    can_split: bool = True,
    split_aces_locked: bool = False,
) -> Action:
    """Recommend an action under the fixed rule preset.

    Availability flags apply to this hand, not to a different table rule set.
    Doubles and splits require two cards even when their flags are True.
    For a split ace already given its one additional card, set
    split_aces_locked=True: the hand must stand. Otherwise, unavailable
    splits fall back to total-based play, with a non-splittable A/A hitting.

    A total of 21 returns Stand. Busts and hands with fewer than two cards
    raise ValueError because there is no decision to train on them.
    """
    if len(player_hand) < 2:
        raise ValueError("Strategy requires at least two player cards")
    hand = evaluate_hand(player_hand)
    if hand.is_bust:
        raise ValueError("Cannot recommend an action for a busted hand")
    if split_aces_locked or hand.total == 21:
        return Action.STAND

    up = card_value(dealer_upcard)
    double_allowed = can_double and len(player_hand) == 2
    split_allowed = can_split and len(player_hand) == 2
    pair = hand.pair_rank

    if split_allowed and pair is not None:
        if pair in ("A", "8"):
            return Action.SPLIT
        if pair == "10":
            return Action.STAND
        if pair == "9":
            return Action.SPLIT if up in (2, 3, 4, 5, 6, 8, 9) else Action.STAND
        split_limits = {"2": (2, 7), "3": (2, 7), "4": (5, 6),
                        "6": (2, 6), "7": (2, 7)}
        if pair in split_limits:
            low, high = split_limits[pair]
            return Action.SPLIT if low <= up <= high else Action.HIT
        # A pair of fives is played as hard ten.

    total = hand.total
    if hand.is_soft:
        if total >= 20:
            return Action.STAND
        if total == 19:
            return Action.DOUBLE if double_allowed and up == 6 else Action.STAND
        if total == 18:
            if 2 <= up <= 6:
                return Action.DOUBLE if double_allowed else Action.STAND
            return Action.STAND if up in (7, 8) else Action.HIT
        doubling_ranges = {17: (3, 6), 16: (4, 6), 15: (4, 6),
                           14: (5, 6), 13: (5, 6)}
        if total in doubling_ranges:
            low, high = doubling_ranges[total]
            if double_allowed and low <= up <= high:
                return Action.DOUBLE
        return Action.HIT

    if total >= 17:
        return Action.STAND
    if 13 <= total <= 16:
        return Action.STAND if 2 <= up <= 6 else Action.HIT
    if total == 12:
        return Action.STAND if 4 <= up <= 6 else Action.HIT
    if total == 11 and double_allowed:
        return Action.DOUBLE
    if total == 10 and double_allowed and 2 <= up <= 9:
        return Action.DOUBLE
    if total == 9 and double_allowed and 3 <= up <= 6:
        return Action.DOUBLE
    return Action.HIT
