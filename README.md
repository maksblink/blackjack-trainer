# Blackjack Trainer

A Python project for blackjack practice. The current implementation provides
playing-card and shoe models, plus a command-line entry point. Interactive
training modes are not yet implemented.

## Features

- Immutable cards with validated ranks and suits.
- Standard 52-card decks without jokers.
- Configurable multi-deck shoes; six decks (312 cards) by default.
- Shuffling with an optional seeded random generator.
- Single-card and batch draws, with remaining-card and deck counts.
- Explicit exhaustion errors and full-shoe reshuffling.

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

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover card validation, deck composition, draw order and boundaries,
shoe exhaustion, seeded shuffling, and restoration of previously drawn cards.
