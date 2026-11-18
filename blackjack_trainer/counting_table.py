"""Stepwise blackjack rounds for visible-card Hi-Lo practice."""

from collections import deque
from dataclasses import dataclass, field
import random
import re

from blackjack_trainer.cards import Card
from blackjack_trainer.counting import CountFeedback, hi_lo_value
from blackjack_trainer.hands import evaluate_hand
from blackjack_trainer.shoe import Shoe, ShoeExhaustedError
from blackjack_trainer.strategy import Action, basic_strategy


@dataclass
class TableHand:
    cards: list[Card] = field(default_factory=list)
    from_split: bool = False
    split_aces: bool = False
    status: str = ''


@dataclass(frozen=True)
class _Event:
    kind: str
    player: int = 0
    hand: int = 0
    card: Card | None = None
    text: str = ''


def _plan_round(cards: tuple[Card, ...], player_count: int) -> list[_Event]:
    """Prepare privately; do not consume real shoe cards or count unseen cards.

    Planning allows an incomplete tail to be reshuffled BEFORE a round starts.
    Rules: H17, DAS, peek, four hands per seat, no resplitting/hitting split aces.
    """
    events = []
    cursor = iter(cards)
    players = [[TableHand()] for _ in range(player_count)]
    dealer = []

    def draw(kind, player=0, hand=0):
        try:
            card = next(cursor)
        except StopIteration as error:
            raise ShoeExhaustedError('Not enough cards for a complete round') from error
        events.append(_Event(kind, player, hand, card))
        return card

    for p in range(player_count):
        players[p][0].cards.append(draw('player_card', p))
    dealer.append(draw('dealer_up'))
    for p in range(player_count):
        players[p][0].cards.append(draw('player_card', p))
    dealer.append(draw('dealer_hole'))
    if evaluate_hand(dealer).is_blackjack:
        events.append(_Event('reveal', text='Dealer reveals blackjack.'))
        events.append(_Event('finish', text='Round complete. Press Space to hide the table and answer.'))
        return events
    if dealer[0].rank in ('A', '10', 'J', 'Q', 'K'):
        events.append(_Event('notice', text='Dealer checks for blackjack: no blackjack.'))
    for p, hands in enumerate(players):
        h = 0
        while h < len(hands):
            hand = hands[h]
            if len(hand.cards) == 1:
                hand.cards.append(draw('player_card', p, h))
            result = evaluate_hand(hand.cards, from_split=hand.from_split)
            if hand.split_aces:
                events.append(_Event('status', p, h, text='Stand (split aces)'))
                h += 1
                continue
            if result.is_blackjack:
                events.append(_Event('status', p, h, text='Blackjack'))
                h += 1
                continue
            if result.is_bust:
                events.append(_Event('status', p, h, text='Bust'))
                h += 1
                continue
            action = basic_strategy(hand.cards, dealer[0], can_split=len(hands) < 4)
            if action == Action.SPLIT:
                events.append(_Event('split', p, h, text='Split'))
                first, second = hand.cards
                aces = first.rank == 'A'
                hands[h:h+1] = [TableHand([first], True, aces), TableHand([second], True, aces)]
                continue
            events.append(_Event('status', p, h, text=action.label))
            if action == Action.STAND:
                h += 1
            elif action == Action.DOUBLE:
                hand.cards.append(draw('player_card', p, h))
                events.append(_Event('status', p, h, text='Bust' if evaluate_hand(hand.cards).is_bust else 'Stand (doubled)'))
                h += 1
            else:
                hand.cards.append(draw('player_card', p, h))
    events.append(_Event('reveal', text='Dealer reveals the hole card.'))
    # No dealer draws are needed if every player hand is bust or a natural.
    live = any(not (r.is_bust or r.is_blackjack)
               for hands in players for hand in hands
               for r in [evaluate_hand(hand.cards, from_split=hand.from_split)])
    if live:
        while True:
            result = evaluate_hand(dealer)
            if result.total < 17 or (result.total == 17 and result.is_soft):
                events.append(_Event('notice', text='Dealer hits.'))
                dealer.append(draw('dealer_up'))
            else:
                break
    events.append(_Event('notice', text='Dealer busts.' if evaluate_hand(dealer).is_bust else 'Dealer finishes.'))
    events.append(_Event('finish', text='Round complete. Press Space to hide the table and answer.'))
    return events


class CountingTableSession:
    """Only exposed cards affect the count; each completed round is scored once."""

    def __init__(self, *, players: int = 3, seed: int | None = None,
                 round_limit: int | None = None, shoe: Shoe | None = None) -> None:
        if isinstance(players, bool) or not isinstance(players, int):
            raise TypeError('players must be an integer')
        if not 1 <= players <= 7:
            raise ValueError('players must be between 1 and 7')
        if round_limit is not None:
            if isinstance(round_limit, bool) or not isinstance(round_limit, int):
                raise TypeError('round_limit must be an integer')
            if round_limit < 1:
                raise ValueError('round_limit must be positive')
        if shoe is not None and shoe.position:
            raise ValueError('Counting practice requires an undrawn shoe')
        self.shoe = shoe if shoe is not None else Shoe(rng=random.Random(seed))
        self.player_count = players
        self.round_limit = round_limit
        self.shoe_number = 1
        self.running_count = 0
        self.answered = self.correct = 0
        self.streak = self.best_streak = 0
        self.total_absolute_error = 0
        self.total_cards_seen = self.checked_cards = 0
        self.feedback: CountFeedback | None = None
        self.phase = 'ready'
        self.start_round()

    @property
    def completed(self):
        return self.round_limit is not None and self.answered >= self.round_limit

    @property
    def incorrect(self):
        return self.answered - self.correct

    @property
    def accuracy(self):
        return 100 * self.correct / self.answered if self.answered else 0.0

    @property
    def mean_absolute_error(self):
        return self.total_absolute_error / self.answered if self.answered else 0.0

    def start_round(self) -> bool:
        if self.completed or self.phase not in ('ready', 'feedback'):
            return False
        new_shoe = self.shoe.position == 0
        try:
            plan = _plan_round(self.shoe.cards[self.shoe.position:], self.player_count)
        except ShoeExhaustedError:
            self.shoe.shuffle()
            self.shoe_number += 1
            self.running_count = 0
            new_shoe = True
            try:
                plan = _plan_round(self.shoe.cards, self.player_count)
            except ShoeExhaustedError as error:
                raise RuntimeError('This shoe cannot complete the round. Use the default six-deck shoe.') from error
        self._events = deque(plan)
        self.players = [[TableHand()] for _ in range(self.player_count)]
        self.dealer: list[Card | None] = []
        self._hole: Card | None = None
        self.round_cards_seen = 0
        self.feedback = None
        self.phase = 'playing'
        self.message = ('New shoe: count starts at 0. ' if new_shoe else '') + 'Press Space to deal.'
        return True

    def _see(self, card):
        self.running_count += hi_lo_value(card)
        self.round_cards_seen += 1
        self.total_cards_seen += 1

    def advance(self) -> bool:
        if self.phase == 'round_end':
            self.players = [[] for _ in range(self.player_count)]
            self.dealer = []
            self.phase = 'answer'
            self.message = 'What is the cumulative running count after this round?'
            return True
        if self.phase != 'playing':
            return False
        event = self._events.popleft()
        if event.kind in ('player_card', 'dealer_up', 'dealer_hole'):
            card = self.shoe.draw()
            if card != event.card:
                raise RuntimeError('The shoe was changed during a round.')
            if event.kind == 'dealer_hole':
                self._hole = card
                self.dealer.append(None)
                self.message = 'Dealer receives a face-down card.'
            elif event.kind == 'dealer_up':
                self.dealer.append(card)
                self._see(card)
                self.message = 'Dealer receives a face-up card.'
            else:
                hand = self.players[event.player][event.hand]
                hand.cards.append(card)
                self._see(card)
                self.message = f'Player {event.player+1}, hand {event.hand+1}: receives a card.'
        elif event.kind == 'reveal':
            if self._hole is None or len(self.dealer) < 2 or self.dealer[1] is not None:
                raise RuntimeError('Invalid hole-card reveal.')
            self.dealer[1] = self._hole
            self._see(self._hole)
            self._hole = None
            self.message = event.text
        elif event.kind == 'split':
            hands = self.players[event.player]
            first, second = hands[event.hand].cards
            hands[event.hand:event.hand+1] = [
                TableHand([first], True, first.rank == 'A'),
                TableHand([second], True, first.rank == 'A'),
            ]
            self.message = f'Player {event.player+1}: split.'
        elif event.kind == 'status':
            self.players[event.player][event.hand].status = event.text
            self.message = f'Player {event.player+1}, hand {event.hand+1}: {event.text}.'
        else:
            self.message = event.text
            if event.kind == 'finish':
                self.phase = 'round_end'
        return True

    def submit(self, answer: str) -> CountFeedback:
        if self.phase != 'answer':
            raise ValueError('Finish the round before answering, and answer only once.')
        if not isinstance(answer, str) or re.fullmatch(r'[+-]?[0-9]+', answer.strip()) is None:
            raise ValueError('Enter a whole number, for example -2, 0, or +3.')
        try:
            chosen = int(answer.strip())
        except ValueError as error:
            raise ValueError('Enter a shorter whole number.') from error
        if abs(chosen) > 1000000:
            raise ValueError('Enter a count between -1000000 and 1000000.')
        self.feedback = CountFeedback(chosen, self.running_count)
        self.answered += 1
        self.correct += self.feedback.correct
        self.checked_cards += self.round_cards_seen
        self.total_absolute_error += abs(chosen - self.running_count)
        self.streak = self.streak + 1 if self.feedback.correct else 0
        self.best_streak = max(self.best_streak, self.streak)
        self.phase = 'feedback'
        return self.feedback
