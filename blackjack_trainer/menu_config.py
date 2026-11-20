"""Validate launcher fields without importing a graphical toolkit."""

from dataclasses import dataclass
from blackjack_trainer.step_timer import validate_intervals

MODES = {
    'Basic strategy': 'gui',
    'Hi-Lo: single cards': 'count',
    'Hi-Lo: card series': 'count-series',
    'Hi-Lo: full table': 'count-table',
}


@dataclass(frozen=True)
class MenuConfig:
    mode: str
    round_limit: int | None = None
    seed: int | None = None
    series_size: int = 10
    players: int = 3
    interval_min: float | None = None
    interval_max: float | None = None


def _integer(text, label, *, optional=False, positive=True):
    value = text.strip()
    if optional and not value:
        return None
    try:
        number = int(value)
    except ValueError as error:
        raise ValueError(f'{label} must be a whole number.') from error
    if positive and number < 1:
        raise ValueError(f'{label} must be positive.')
    return number


def parse_menu_config(*, mode, rounds='', seed='', series_size='10', players='3',
                      automatic=False, interval_min='0.5', interval_max='3'):
    if mode not in MODES:
        raise ValueError('Choose a training mode.')
    selected = MODES[mode]
    limit = _integer(rounds, 'Question limit', optional=True)
    random_seed = _integer(seed, 'Seed', optional=True, positive=False)
    size = _integer(series_size, 'Series length') if selected == 'count-series' else 10
    seats = _integer(players, 'Players') if selected == 'count-table' else 3
    if not 1 <= seats <= 7:
        raise ValueError('Players must be between 1 and 7.')
    low = high = None
    if selected == 'count-table' and automatic:
        try:
            low, high = float(interval_min.strip()), float(interval_max.strip())
        except ValueError as error:
            raise ValueError('Tempo bounds must be numbers in seconds (use a decimal point).') from error
        validate_intervals(low, high)
    return MenuConfig(selected, limit, random_seed, size, seats, low, high)
