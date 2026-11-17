# Blackjack Trainer

Practice blackjack opening decisions in the terminal or a Tkinter desktop GUI. Choose Hit, Stand,
Double, or Split, check the recommended action, and track session accuracy.
The trainer uses a six-deck shoe and a fixed H17/DAS/no-surrender strategy.

## Features

- Interactive terminal training with immediate feedback and session statistics.
- Desktop GUI with drawn cards, action buttons, keyboard shortcuts, and a quit confirmation.
- Reproducible shuffles and optional question limits.

- Immutable cards with validated ranks and suits.
- Standard 52-card decks without jokers.
- Configurable multi-deck shoes; six decks (312 cards) by default.
- Shuffling with an optional seeded random generator.
- Single-card and batch draws, with remaining-card and deck counts.
- Explicit exhaustion errors and full-shoe reshuffling.
- Hand totals with automatic ace adjustment (1 or 11).
- Soft/hard classification, pair detection, blackjack, and bust detection.
- Hit, Stand, Double, and Split recommendations for a fixed H17/DAS rule preset.
- Per-hand action availability and locked split-ace handling.

## Requirements

- Python 3.10 or newer
- GUI mode: Tkinter and a graphical desktop

No third-party runtime dependencies are required. Development and testing use
pytest, installed through the `dev` extra.

## Run

From the project root, with the project's virtual environment active:

```bash
python -m blackjack_trainer
# Explicit terminal mode:
python -m blackjack_trainer cli
# Desktop GUI:
python -m blackjack_trainer gui
# A reproducible session of 20 answered questions:
python -m blackjack_trainer cli --seed 42 --rounds 20
# Version and command help:
python -m blackjack_trainer --version
python -m blackjack_trainer --help
```

After an editable installation, `blackjack-trainer cli` also works.

| Input | Action |
| --- | --- |
| `H` | Hit |
| `S` | Stand |
| `D` | Double |
| `P` | Split |
| `Q` | Quit |
| Enter after feedback | Next question |

Inputs are case-insensitive. Invalid input retries the same question without
changing the score. Each answered question is scored once. Quit, end-of-input,
and Ctrl+C show a session summary; unanswered questions do not count.

This mode trains **only the first decision**. Each question draws two player
cards and one dealer upcard; it does not play out the chosen action or the
dealer's hand. A natural blackjack is displayed as such and expects Stand
under the trainer's action convention. Choosing Split on a non-pair is treated
as an incorrect answer.

The trainer reshuffles before a question if fewer than three cards remain.
Statistics persist across reshuffles, but reset when the app restarts. Accuracy
measures agreement with the strategy, not winnings. No files are saved by this
mode, and future shoe cards are not printed.

In PyCharm, run module `blackjack_trainer` with parameter `cli` and the project
root as the working directory.

## Desktop GUI

```bash
python -m blackjack_trainer gui
python -m blackjack_trainer gui --seed 42 --rounds 20
```

The window shows the two player cards, the dealer upcard, feedback, and session
statistics. Cards retain their actual suits from the shoe. Click an action or
press `H`, `S`, `D`, or `P`. After answering, press Enter or Space to deal the
next hand. Answer buttons are disabled after scoring, and Next is disabled
until an answer is submitted.

Press `Q` or Esc, or close the window, to see the exit confirmation and session
summary. Canceling the dialog preserves the current question, shoe position,
and score. With `--rounds`, the final feedback remains visible after the limit
is reached, and further answers and deals are disabled.

The GUI uses the same session and strategy engine as the terminal trainer.
It practices opening decisions only. It does not play out hands, settle bets,
or save session data. The default mode remains `cli` when no mode is supplied.
The minimum window size is 820 × 680 pixels.

### Check Tkinter

Run this with the same interpreter used by the project:

```bash
python -m tkinter
```

A small test window should appear. On Linux, Tkinter may require a separate
OS package matching your Python installation. For a custom Python 3.14
interpreter, installing Tkinter for a different system Python is insufficient.
Tkinter is not a pip dependency. Without Tkinter or a graphical display, the
terminal mode remains available.

In PyCharm, select module `blackjack_trainer`, parameter `gui`, and the project's
`.venv` interpreter. Use the project root as the working directory.

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

## Basic strategy

The engine uses a total-dependent multi-deck policy for **H17 / DAS / no
surrender**: the dealer hits soft 17, doubling after a split is allowed, and
surrender is unavailable. It assumes dealer peek and doubling on any first
two cards. The preset is intended for the default six-deck shoe; changing the
shoe size does not change the strategy chart.

```python
from blackjack_trainer.cards import Card
from blackjack_trainer.strategy import basic_strategy

hand = [Card("A", "♠"), Card("7", "♥")]
upcard = Card("2", "♣")
action = basic_strategy(hand, upcard)
print(action.value, action.label)  # D Double

action = basic_strategy(hand, upcard, can_double=False)
print(action.value, action.label)  # S Stand
```

The returned `Action` enum provides `HIT`, `STAND`, `DOUBLE`, and `SPLIT`, with
codes `H`, `S`, `D`, and `P`. The engine evaluates pairs before soft and hard
totals. It does not use the running count or remaining shoe composition.

Set `can_double=False` or `can_split=False` when an action is unavailable for
this hand. These flags do not select a different table-wide ruleset such as
no-DAS. Hands with more than two cards cannot double or split. Unavailable
splits fall back to total-based play; a non-splittable A/A uses Hit as an
explicit fallback. This fallback is not an optimization for unusual rules
allowing unrestricted play after splitting aces.

After a split ace receives its one additional card, pass
`split_aces_locked=True` to require Stand. The caller supplies this context;
it cannot be inferred from the cards alone. A total of 21 returns Stand.
Busted hands and hands with fewer than two cards raise `ValueError`.

Reference: [Wizard of Odds: multi-deck strategy and H17 adjustments](https://wizardofodds.com/games/blackjack/strategy/4-decks/).

## Development setup

From the project root, activate the project's virtual environment and install
the package with its development dependencies:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.
If the environment does not exist yet, create it with `python -m venv .venv`.

## Tests

Run all tests from the project root:

```bash
python -m pytest
```

For verbose results or a single module:

```bash
python -m pytest -v
python -m pytest tests/test_hands.py -v
python -m pytest tests/test_strategy.py -v
python -m pytest tests/test_training.py tests/test_cli.py -v
python -m pytest tests/test_gui_controller.py tests/test_gui.py tests/test_gui_entrypoint.py -v
```

Pytest discovers tests in `tests/`, using the configuration in `pyproject.toml`.
Card, shoe, and hand-evaluation tests use `unittest.TestCase` and are executed
by pytest without conversion. Strategy tests use native pytest parametrization. Pytest 9 also supports their `subTest()` cases. New tests can use
native pytest functions, plain assertions, fixtures, and parametrization.

In PyCharm, select the project's `.venv` interpreter and set the default test
runner to **pytest** under **Settings → Tools → Python Integrated Tools**.
Existing unittest run configurations may need to be replaced with pytest
configurations.

Reference: [pytest's unittest compatibility](https://docs.pytest.org/en/stable/how-to/unittest.html).

Tests cover card validation, deck composition, draw order and boundaries,
shoe exhaustion, seeded shuffling, and restoration of previously drawn cards.
Hand tests cover multiple aces, soft-to-hard transitions, naturals, split hands,
busts, and pairs. All rank combinations of up to three cards are also checked
against an independent enumeration of ace values.

Strategy tests cover hard, soft, and pair chart cells, unavailable actions,
multicard hands, split aces, and equivalent ten-valued dealer cards.

Session and CLI tests cover scoring, invalid input, quit/EOF/Ctrl+C, question
limits, reshuffling, reproducible questions, and command-line arguments.

GUI controller tests run without Tkinter. Window callback tests require Tkinter
but no display. The real-window smoke test is skipped when a graphical display
is unavailable; run the suite on a desktop to exercise it.
