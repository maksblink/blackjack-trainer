from collections import Counter
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from blackjack_trainer.cards import Card
from blackjack_trainer.counting import hi_lo_value
from blackjack_trainer.counting_table import CountingTableSession
from blackjack_trainer.hands import evaluate_hand
from blackjack_trainer.shoe import Shoe


class FixedShoe(Shoe):
    def __init__(self, ranks):
        super().__init__(shuffle=False)
        self._fixture = [Card(rank, '♠') for rank in ranks]
        self._cards = self._fixture.copy()
        self.shuffles = 0

    def shuffle(self):
        self._cards = self._fixture.copy()
        self._position = 0
        self.shuffles += 1


def session(ranks):
    return CountingTableSession(players=1, shoe=FixedShoe(ranks))


def finish(s):
    steps = 0
    while s.phase == 'playing':
        s.advance()
        steps += 1
        assert steps < 1000
    assert s.phase == 'round_end'


def test_hole_card_is_counted_only_on_reveal():
    s = session(['9','A','7','K'])
    assert s.shoe.position == s.running_count == 0
    for _ in range(4):
        s.advance()
    assert s.dealer == [Card('A','♠'), None]
    assert s.shoe.position == 4 and s.total_cards_seen == 3
    assert s.running_count == -1
    assert 'K' not in s.message
    s.advance()
    assert s.dealer[1] == Card('K','♠')
    assert s.running_count == -2 and s.total_cards_seen == 4
    finish(s)
    assert s.shoe.position == 4  # dealer blackjack stops all player actions
    assert s.players[0][0].status == ''


def test_dealing_order():
    s = CountingTableSession(players=3, seed=42)
    order = s.shoe.cards[:8]
    for _ in range(8):
        s.advance()
    for p in range(3):
        assert s.players[p][0].cards == [order[p], order[p+4]]
    assert s.dealer == [order[3], None]
    assert s.running_count == sum(hi_lo_value(c) for c in order[:7])


def test_split_double_and_count_once():
    s = session(['8','6','8','10','3','2','2','K','5'])
    finish(s)
    assert [len(h.cards) for h in s.players[0]] == [3,3]
    assert [h.status for h in s.players[0]] == ['Stand (doubled)']*2
    assert all(h.from_split for h in s.players[0])
    assert evaluate_hand(s.dealer).total == 21
    assert s.shoe.position == s.total_cards_seen == 9
    assert s.running_count == sum(map(hi_lo_value, s.shoe.cards))


def test_split_aces_no_resplit_or_extra_hits():
    s = session(['A','6','A','10','A','9','5'])
    finish(s)
    assert [len(h.cards) for h in s.players[0]] == [2,2]
    assert all(h.status == 'Stand (split aces)' for h in s.players[0])
    assert [c.rank for c in s.players[0][0].cards] == ['A','A']


def test_max_four_hands():
    s = session(['8','6','8','10','8','8','8','10','10','10','5'])
    finish(s)
    assert len(s.players[0]) == 4
    assert [c.rank for c in s.players[0][0].cards] == ['8','8']
    assert s.players[0][0].status == 'Stand'


def test_split_twenty_one_is_not_natural():
    s = session(['A','6','A','10','K','10','5'])
    finish(s)
    assert all(not evaluate_hand(h.cards, from_split=h.from_split).is_blackjack for h in s.players[0])
    assert len(s.dealer) == 3


def test_dealer_hits_soft_seventeen():
    s = session(['10','A','8','6','2'])
    finish(s)
    assert [c.rank for c in s.dealer] == ['A','6','2']
    assert evaluate_hand(s.dealer).total == 19


@pytest.mark.parametrize('ranks,expected_draws', [(['A','6','K','10'],4), (['10','10','6','6','K'],5)])
def test_no_dealer_draw_after_all_bust_or_natural(ranks, expected_draws):
    s = session(ranks)
    finish(s)
    assert len(s.dealer) == 2 and all(c is not None for c in s.dealer)
    assert s.shoe.position == expected_draws


def test_reshuffle_before_round_never_midway():
    s = session(['10','10','10','7','2'])
    finish(s)
    assert s.shoe.remaining == 1 and s.shoe.shuffles == 0
    s.advance()
    s.submit(str(s.running_count))
    assert s.start_round()
    assert s.shoe.shuffles == 1 and s.shoe_number == 2
    assert s.running_count == s.shoe.position == 0
    assert s.total_cards_seen == s.checked_cards == 4
    assert 'New shoe' in s.message
    finish(s)
    assert s.shoe.shuffles == 1


def test_hide_answer_stats_limit():
    s = CountingTableSession(players=2, seed=5, round_limit=3)
    for error in (0, 2, 0):
        finish(s)
        count = s.running_count
        assert s.advance()
        assert not s.dealer and not any(s.players)
        assert s.phase == 'answer'
        assert not s.advance() and not s.start_round()
        for invalid in ('', '1.2', '1000001'):
            with pytest.raises(ValueError):
                s.submit(invalid)
        s.submit(str(count + error))
        assert s.running_count == count
        with pytest.raises(ValueError):
            s.submit('0')
        if not s.completed:
            s.start_round()
            assert s.running_count == count
    assert s.answered == 3 and s.correct == 2 and s.incorrect == 1
    assert s.accuracy == pytest.approx(200/3)
    assert s.mean_absolute_error == pytest.approx(2/3)
    assert s.streak == s.best_streak == 1
    assert s.checked_cards == s.total_cards_seen
    before = s.shoe.position
    assert not s.start_round() and not s.advance()
    assert s.shoe.position == before


@pytest.mark.parametrize('players', range(1,8))
def test_many_rounds_conserve_cards_and_count(players):
    a = CountingTableSession(players=players, seed=17)
    b = CountingTableSession(players=players, seed=17)
    seen = Counter()
    shoe_number = 1
    for _ in range(80):
        if a.shoe_number != shoe_number:
            shoe_number = a.shoe_number
            seen.clear()
        before = a.shoe.position
        finish(a)
        finish(b)
        assert a.dealer == b.dealer and a.players == b.players
        assert a.running_count == b.running_count
        assert all(len(hands) <= 4 for hands in a.players)
        drawn = a.shoe.cards[before:a.shoe.position]
        visible = a.dealer + [c for hands in a.players for hand in hands for c in hand.cards]
        assert Counter(visible) == Counter(drawn)
        seen.update(drawn)
        assert all(n <= 6 for n in seen.values())
        assert a.running_count == sum(hi_lo_value(c)*n for c,n in seen.items())
        for s in (a,b):
            s.advance()
            s.submit(str(s.running_count))
            s.start_round()


@pytest.mark.parametrize('kwargs', [{'players':0},{'players':8},{'players':True},{'players':1.5},
    {'round_limit':0},{'round_limit':False},{'round_limit':2.5}])
def test_invalid_arguments(kwargs):
    with pytest.raises((ValueError,TypeError)):
        CountingTableSession(**kwargs)


def test_early_answer_and_next_round_rejected():
    s = CountingTableSession()
    with pytest.raises(ValueError):
        s.submit('0')
    assert not s.start_round()
    assert s.shoe.position == s.answered == 0


@pytest.mark.parametrize('flags,players', [([],3),(['--players','1'],1),(['--players','7'],7)])
def test_cli_dispatch(monkeypatch, flags, players):
    import sys
    from blackjack_trainer.__main__ import main
    launch = Mock()
    monkeypatch.setitem(sys.modules, 'blackjack_trainer.counting_table_gui',
                        SimpleNamespace(launch_counting_table_gui=launch))
    monkeypatch.setattr(sys,'argv',['trainer','count-table',*flags,'--seed','7','--rounds','3'])
    main()
    launch.assert_called_once_with(players=players,seed=7,round_limit=3)


@pytest.mark.parametrize('args', [['count-table','--players','0'],['count-table','--players','8'],
    ['count-table','--players','1.5'],['count','--players','3'],['count-table','-n','5']])
def test_cli_rejects_invalid(monkeypatch,args):
    import sys
    from blackjack_trainer.__main__ import main
    monkeypatch.setattr(sys,'argv',['trainer',*args])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2


def test_gui_callbacks(monkeypatch):
    pytest.importorskip('tkinter')
    import blackjack_trainer.counting_table_gui as gui
    app = gui.CountingTableApp.__new__(gui.CountingTableApp)
    app.session = CountingTableSession(players=1,seed=2,round_limit=1)
    app._closing = False
    for name in ('answer','refresh','root','message'):
        setattr(app,name,Mock())
    app.on_enter()
    assert app.session.shoe.position == 0
    app.on_space()
    assert app.session.shoe.position == 1
    monkeypatch.setattr(gui.messagebox,'askokcancel',lambda *a,**k:False)
    before = app.session.shoe.position
    app.on_close()
    app.root.destroy.assert_not_called()
    assert app.session.shoe.position == before
    finish(app.session)
    app.on_space()
    assert app.session.phase == 'answer'
    app.answer.get.return_value = str(app.session.running_count)
    app.on_enter()
    assert app.session.completed
    app.on_check()
    app.on_enter()
    assert app.session.answered == 1


def test_real_table_window():
    tk = pytest.importorskip('tkinter')
    from blackjack_trainer.counting_table_gui import CountingTableApp
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('No graphical display available')
    try:
        s = CountingTableSession(players=1,round_limit=1,seed=4)
        app = CountingTableApp(root,s)
        root.update()
        while s.phase in ('playing','round_end'):
            app.on_space()
            root.update()
        assert s.phase == 'answer'
        app.answer.set(str(s.running_count))
        app.on_enter()
        root.update()
        assert s.completed
    finally:
        root.destroy()
