# Blackjack Trainer

A Python project for blackjack practice. The current implementation provides
playing-card and shoe models, hand evaluation, and a command-line entry point. Interactive
training modes are not yet implemented.

## Features

- Immutable cards with validated ranks and suits.
- Standard 52-card decks without jokers.
- Configurable multi-deck shoes; six decks (312 cards) by default.
- Shuffling with an optional seeded random generator.
- Single-card and batch draws, with remaining-card and deck counts.
- Explicit exhaustion errors and full-shoe reshuffling.
- Hand totals with automatic ace adjustment (1 or 11).
- Soft/hard classification, pair detection, blackjack, and bust detection.

## Requirements

- Python 3.10 or newer

No third-party runtime dependencies are required.

## Run

From the project root:

```bash
python -m blackjack_trainer
python -m blackjack_trainer --version
```

The command-line entry point displays the application name or version.

## Use the card and shoe models

```python
import random

from blackjack_trainer.cards import Card
from blackjack_trainer.shoe import Shoe, ShoeExhaustedError

ace = Card("A", "♠")
print(ace)  # A♠

shoe = Shoe(number_of_decks=6, rng=random.Random(42))
hand = shoe.draw_many(2)
dealer_upcard = shoe.draw()
print([str(card) for card in hand], str(dealer_upcard))
print(shoe.remaining)  # 309
print(shoe.remaining_decks)  # 309 / 52

try:
    shoe.draw_many(310)
except ShoeExhaustedError:
    print("Not enough cards; no additional cards were consumed.")

shoe.shuffle()  # Restore all 312 cards, shuffle, and reset the position.
```

Drawing never triggers an automatic reshuffle. `draw_many()` either returns
all requested cards or leaves the shoe unchanged. `shoe.cards` is an immutable
snapshot of the entire shoe in dealing order. Equal rank/suit cards can appear
multiple times in a multi-deck shoe.

## Evaluate a hand

```python
from blackjack_trainer.cards import Card
from blackjack_trainer.hands import evaluate_hand

hand = [Card("A", "♠"), Card("6", "♥")]
result = evaluate_hand(hand)
print(result.total, result.is_soft)  # 17 True

hand.append(Card("10", "♣"))
result = evaluate_hand(hand)
print(result.total, result.is_soft)  # 17 False
print(result.is_bust, result.is_blackjack)  # False False

natural = evaluate_hand([Card("A", "♠"), Card("K", "♥")])
print(natural.is_blackjack)  # True
split_hand = evaluate_hand([Card("A", "♠"), Card("K", "♥")], from_split=True)
print(split_hand.is_blackjack)  # False
```

A soft hand has an ace currently counted as 11. A blackjack is a two-card 21
from an unsplit hand; a three-card 21 or a split-hand 21 is not a blackjack.
Pass `from_split=True` when evaluating a hand created by splitting.

`evaluate_hand()` returns an immutable summary with `total`, `is_soft`,
`is_blackjack`, `is_bust`, and `pair_rank`. An empty hand has total zero.
The convenience functions `hand_value()`, `is_soft()`, and `pair_rank()` are
also available from `blackjack_trainer.hands`.

Pair detection requires exactly two cards. All ten-valued ranks are grouped
as `"10"`, so J/K counts as a pair for this model. Pair detection does not
check whether a split is allowed under a particular table's rules.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover card validation, deck composition, draw order and boundaries,
shoe exhaustion, seeded shuffling, and restoration of previously drawn cards.
Hand tests cover multiple aces, soft-to-hard transitions, naturals, split hands,
busts, and pairs. All rank combinations of up to three cards are also checked
against an independent enumeration of ace values.
