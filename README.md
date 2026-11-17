# Blackjack Trainer

A Python project for practicing blackjack basic strategy and Hi-Lo card counting.

## Project status

The project currently provides a package structure and a command-line entry
point. Training modes are under development.

## Requirements

- Python 3.10 or newer

No third-party runtime dependencies are required at this stage.

## Run

From the project root:

```bash
python -m blackjack_trainer
python -m blackjack_trainer --version
```

## Development roadmap

- [x] Initialize the project structure
- [ ] Add card and shoe models
- [ ] Implement hand evaluation
- [ ] Implement the basic strategy engine
- [ ] Add a terminal strategy trainer
- [ ] Add a graphical strategy trainer
- [ ] Add keyboard controls and session exports
- [ ] Implement automated round simulation
- [ ] Add a Hi-Lo counting trainer
- [ ] Cover session lifecycle and edge cases
- [ ] Complete documentation and configure CI

## Development approach

Features are introduced incrementally, with focused commits and tests for
game logic and session behavior.
