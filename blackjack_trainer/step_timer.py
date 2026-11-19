"""One cancellable UI timer with independently sampled step delays."""

import math
import random


def validate_intervals(minimum, maximum):
    if minimum is None and maximum is None:
        return
    if minimum is None or maximum is None:
        raise ValueError('Provide both --interval-min and --interval-max.')
    for value in (minimum, maximum):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Intervals must be numbers in seconds.')
        if not math.isfinite(value) or not 0 < value <= 2147483:
            raise ValueError('Intervals must be finite, positive, and at most 2147483 seconds.')
    if minimum > maximum:
        raise ValueError('--interval-min must not exceed --interval-max.')


class StepTimer:
    """Schedule one step at a time; step returns whether to continue.

    Pause cancels the pending step. Resume draws a fresh full delay. Tokens make
    callbacks harmless even if they arrive after cancellation or rescheduling.
    The scheduler supplies Tk-compatible after/after_cancel methods.
    """

    def __init__(self, scheduler, step, minimum, maximum, *, rng=None):
        validate_intervals(minimum, maximum)
        if minimum is None:
            raise ValueError('A timer requires both interval bounds.')
        self.scheduler = scheduler
        self.step = step
        self.minimum, self.maximum = minimum, maximum
        self.rng = rng if rng is not None else random.Random()
        self.running = False
        self.closed = False
        self._pending = None
        self._generation = 0

    def start(self):
        if self.closed or self.running:
            return
        self.running = True
        self._schedule()

    def pause(self):
        self.running = False
        self._generation += 1
        if self._pending is not None:
            self.scheduler.after_cancel(self._pending)
            self._pending = None

    def close(self):
        self.pause()
        self.closed = True

    def _schedule(self):
        if not self.running or self.closed or self._pending is not None:
            return
        delay = self.minimum if self.minimum == self.maximum else self.rng.uniform(self.minimum, self.maximum)
        milliseconds = max(1, round(delay * 1000))
        self._generation += 1
        generation = self._generation
        self._pending = self.scheduler.after(milliseconds, lambda: self._fire(generation))

    def _fire(self, generation):
        if generation != self._generation or not self.running or self.closed:
            return
        self._pending = None
        try:
            continuing = self.step()
        except Exception:
            self.pause()
            raise
        if not continuing:
            self.pause()
        if self.running and not self.closed:
            self._schedule()
