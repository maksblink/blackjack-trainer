from collections import Counter
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from blackjack_trainer.cards import Card, RANKS, SUITS
from blackjack_trainer.counting import CountingSession, hi_lo_value
from blackjack_trainer.shoe import Shoe

@pytest.mark.parametrize('rank,expected', list(zip(RANKS, [1,1,1,1,1,0,0,0,-1,-1,-1,-1,-1])))
@pytest.mark.parametrize('suit', SUITS)
def test_values(rank, expected, suit):
    assert hi_lo_value(Card(rank, suit)) == expected

def test_whole_shoe_and_reset():
    session = CountingSession(seed=42)
    seen, count = Counter(), 0
    for _ in range(312):
        seen[session.card] += 1
        rank = session.card.rank
        count += 1 if rank in ('2','3','4','5','6') else 0 if rank in ('7','8','9') else -1
        assert session.running_count == count
        assert session.submit(str(count)).correct
        if session.shoe.remaining:
            assert session.next_card()
    assert len(seen) == 52 and set(seen.values()) == {6}
    assert count == 0 and session.shoe.remaining == 0
    assert session.next_card()
    assert session.shoe_number == 2 and session.shoe.remaining == 311
    assert session.running_count == hi_lo_value(session.card)
    assert session.answered == session.correct == 312

@pytest.mark.parametrize('answer', ['', ' ', '1.0', '++2', 'hello', '--1', '2 3'])
def test_invalid_input_preserves_state(answer):
    session = CountingSession(seed=1)
    state = (session.card, session.shoe.position, session.running_count)
    with pytest.raises(ValueError):
        session.submit(answer)
    assert session.answered == 0 and session.feedback is None
    assert state == (session.card, session.shoe.position, session.running_count)

def test_wrong_answer_and_duplicate_guard():
    session = CountingSession(seed=2)
    original = session.running_count
    assert not session.next_card()
    assert not session.submit('999').correct
    assert session.running_count == original
    with pytest.raises(ValueError):
        session.submit(str(original))
    assert session.answered == 1
    session.next_card()
    assert session.running_count == original + hi_lo_value(session.card)

def test_limit_keeps_final_card():
    session = CountingSession(round_limit=1)
    card = session.card
    session.submit(f' {session.running_count:+d} ')
    assert session.completed and not session.next_card()
    assert session.card == card and session.shoe.position == 1
    assert session.accuracy == 100

def test_seed_reproducibility():
    a, b = CountingSession(seed=24), CountingSession(seed=24)
    for _ in range(20):
        assert a.card == b.card
        for session in (a, b):
            session.submit(str(session.running_count))
            session.next_card()

@pytest.mark.parametrize('limit', [0, -1, True, 1.5])
def test_bad_limits(limit):
    with pytest.raises((ValueError, TypeError)):
        CountingSession(round_limit=limit)

def test_reject_partially_drawn_shoe():
    shoe = Shoe()
    shoe.draw()
    with pytest.raises(ValueError):
        CountingSession(shoe=shoe)

def test_gui_callbacks_and_cancel(monkeypatch):
    pytest.importorskip('tkinter')
    from blackjack_trainer.counting_gui import CountingApp
    import blackjack_trainer.counting_gui as gui
    app = CountingApp.__new__(CountingApp)
    app.session = CountingSession(seed=1)
    app._closing = False
    app.answer = Mock()
    app.answer.get.return_value = str(app.session.running_count)
    app.message, app.refresh, app.root = Mock(), Mock(), Mock()
    app.on_next()
    assert app.session.shoe.position == 1
    app.on_enter()
    assert app.session.answered == 1
    app.on_check()
    assert app.session.answered == 1
    monkeypatch.setattr(gui.messagebox, 'askokcancel', lambda *a, **k: False)
    app.on_close()
    app.root.destroy.assert_not_called()
    assert app.session.shoe.position == 1
    app.on_enter()
    assert app.session.shoe.position == 2
    app.answer.set.assert_called_with('')

def test_count_entrypoint(monkeypatch):
    import sys
    from blackjack_trainer.__main__ import main
    launch = Mock()
    monkeypatch.setitem(sys.modules, 'blackjack_trainer.counting_gui', SimpleNamespace(launch_counting_gui=launch))
    monkeypatch.setattr(sys, 'argv', ['blackjack-trainer', 'count', '--seed', '7', '--rounds', '2'])
    main()
    launch.assert_called_once_with(seed=7, round_limit=2)
