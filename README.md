# Blackjack Trainer

Practice blackjack opening decisions in the terminal or a Tkinter desktop GUI. Choose Hit, Stand,
Double, or Split, check the recommended action, and track session accuracy.
The trainer uses a six-deck shoe and a fixed H17/DAS/no-surrender strategy.

A separate desktop mode trains the Hi-Lo running count.

## Start menu

```bash
python -m blackjack_trainer menu
```

Choose Basic strategy, Hi-Lo single cards, Hi-Lo card series, or Hi-Lo full
table. Set an optional question limit and seed, the series length, or the number
of players and table tempo. Only settings relevant to the selected mode are
enabled. Leave the limit blank for an unlimited session and the seed blank for
a fresh shuffle. The limit counts hands, cards, series, or rounds respectively.
Automatic table tempo requires positive minimum and maximum delays, with the
minimum no larger than the maximum. Equal values give a fixed delay.

Click Start or press Enter. Invalid fields show a message without starting a
session. Closing a trainer through its existing confirmation returns to the
menu; canceling keeps the trainer open. Menu settings are retained while the
launcher stays open, but each Start creates a fresh session and statistics.
Settings and results are not saved to disk. Quit in the menu closes the app.

`python -m blackjack_trainer menu --seed 42 --rounds 20` prefills the common
fields. All existing direct commands remain available, and omitting the mode
still starts the terminal strategy trainer. In PyCharm, run the module
`blackjack_trainer` with parameter `menu`.

## Features

- Desktop start menu for selecting training modes and session settings.
- Interactive terminal training with immediate feedback and session statistics.
- Desktop GUI with drawn cards, action buttons, keyboard shortcuts, and a quit confirmation.
- Hi-Lo counting practice with one card at a time and running-count feedback.
- Full-table counting with automated player decisions and a hidden dealer card.
- Separate series mode with configurable length, hidden cards at answer time, and series statistics.
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

Card rendering uses Pillow (installed with the package) and DejaVu Sans.
On Ubuntu, install the font with `sudo apt install fonts-dejavu-core`.
Development and testing use pytest, installed through the `dev` extra.

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

## Hi-Lo counting GUI

```bash
python -m blackjack_trainer count
python -m blackjack_trainer count --seed 42 --rounds 20
```

Start from zero. Each displayed card is drawn from a six-deck shoe without
replacement. Add +1 for 2–6, zero for 7–9, and −1 for 10/J/Q/K/A. Enter the
**cumulative running count**, including the current card, then click Check
or press Enter. After feedback, click Next card or press Enter again.
Each card must be answered before proceeding; this mode checks every card.
Invalid input does not consume a card or change the score. Each card is scored
once. A wrong answer never changes the actual count: continue from the correct
count shown in the feedback.

After all 312 cards have been checked, advancing starts a freshly shuffled
shoe. The count resets to zero before its first card is counted, and a new-shoe
message appears. Session statistics persist across shoes. `--rounds` limits
answered cards; the final feedback stays visible. Esc or Quit opens a summary
and confirmation; canceling preserves the current state.

This mode trains running count only. It does not calculate true count, simulate
rounds, recommend bets, or save session results. It uses the same responsive
card renderer as the strategy GUI.

## Hi-Lo series GUI

```bash
python -m blackjack_trainer count-series
python -m blackjack_trainer count-series --series-size 20
python -m blackjack_trainer count-series -n 5 --seed 42 --rounds 10
```

This separate mode shows one card at a time, with 10 cards per series by default.
`--series-size` (or `-n`) accepts a positive integer. Press Space or click Next
card to replace the current card. After viewing the last card, press Space or
click Finish series to hide it and open the answer field. There is no card
history. Enter checks your cumulative running count; after feedback, Enter or
Next series starts another series. Esc opens the quit confirmation.

The count carries over between series, including after a wrong answer: continue
from the correct count in the feedback. Cards are drawn without replacement.
A series never spans two shoes: its actual length is the smaller of the requested
size and the number of cards left. For example, a six-deck shoe with size 10
produces 31 full series and a final series of 2 cards. A size larger than the
shoe produces one series of 312 cards. Only starting the next series after the
last answer reshuffles the shoe and resets the count. The first card of the
new shoe is then included in the new count.

Statistics count **answered series**, not individual cards: correct/incorrect,
accuracy, current/best correct streak, and mean absolute error (the average
absolute difference between submitted and correct counts). Cards checked counts
cards in answered series; cards shown includes any unfinished series. Invalid
input and repeated submissions do not change the score. `--rounds` limits the
number of answered series. Unfinished series are not scored. Statistics persist
across shoes, appear in the quit summary, and reset when the application closes;
no results are saved to disk.

## Hi-Lo table GUI

```bash
python -m blackjack_trainer count-table
python -m blackjack_trainer count-table --players 5
python -m blackjack_trainer count-table --players 3 --seed 42 --rounds 10
```

Watch a full table with 1–7 players (3 by default) and a dealer. Space or Next
step advances one deal, action, or reveal. Players automatically follow the
project's basic strategy. The rules are six decks, H17, double after split,
dealer peek, no surrender, and at most four hands per player. Split aces receive
one additional card each and cannot be resplit. Other pairs may be resplit up
to the four-hand limit. A split-hand 21 is not a natural blackjack.

The dealer's hole card is dealt face down and contributes to the running count
**only when revealed**. A dealer blackjack is revealed after the initial deal
and ends play immediately. Otherwise players finish first, followed by the
dealer. The dealer hits soft 17. When every player hand is bust or a natural,
the hole card is still revealed but no additional dealer draws are needed.

At round end, Space hides the table and opens the running-count question.
Enter checks the answer; the next Enter starts a new round. The count carries
over between rounds until a shuffle, including after an incorrect answer.
Continue from the correct count in the feedback. There is no betting or bankroll
simulation. For large tables or split hands, use the vertical scrollbar.

Rounds never reshuffle midway. A round is privately planned against the remaining
shoe; if there are not enough cards to finish it, those remaining cards are
not exposed, a new shoe is shuffled, and the count resets before dealing.
Future cards and the planned count are not displayed. Cards leave the real shoe
only as each dealing step is shown. The screen announces a new shoe before its
first deal. Unlike series mode, table mode may therefore leave an unused tail.

### Automatic table tempo

```bash
# Independently sampled delay before every step (seconds):
python -m blackjack_trainer count-table --players 3 --interval-min 0.5 --interval-max 3
# Fixed delay:
python -m blackjack_trainer count-table --interval-min 1 --interval-max 1
```

Provide both bounds, with `0 < min <= max`, to enable automatic table play.
Without them, Space retains manual step-by-step control. These options apply
only to `count-table`. Delays are sampled uniformly and independently before
each deal, action, reveal, and the transition from the completed table to the
answer field. Equal bounds give a constant delay. Scheduling uses millisecond
resolution (at least 1 ms); actual rendering and system load can add latency.

Space or the Pause/Resume button pauses or resumes automatic play. Resuming
starts a fresh full delay from the configured range. At the question the timer
stops and the table is hidden. Answer with Enter; after feedback, press Enter or
Next round to start the next round and restart automatic play. The final
answered round remains on screen when `--rounds` is reached.

The exit confirmation suspends the timer. Cancel restores the prior running or
paused state; confirming exit cancels pending callbacks. Tempo uses its own
random generator, so changing delays does not change shoe order for the same
`--seed`. Statistics and scoring are the same in manual and automatic mode.

Statistics count answered rounds: correct/incorrect, accuracy, current/best
correct streak, mean absolute count error, and cards seen/checked. Cards checked
covers answered rounds; cards seen also includes exposed cards in an unfinished
round. A face-down card is not yet seen. Moving already exposed cards during a
split never counts them again. Invalid input and repeated submissions do not
change statistics. `--rounds` limits answered rounds. Esc or Quit shows a summary
and confirmation; canceling preserves the table. Statistics persist across
shuffles but are not saved after closing the application.

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
