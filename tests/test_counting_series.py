from collections import Counter
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from blackjack_trainer.counting import hi_lo_value
from blackjack_trainer.counting_series import CountingSeriesSession
from blackjack_trainer.shoe import Shoe


def finish(session):
    while session.phase == 'showing':
        session.advance()
    assert session.card is None


@pytest.mark.parametrize('size,lengths', [(10, [10]*31+[2]), (1, [1]*312),
                                         (312, [312]), (500, [312]), (100, [100,100,100,12])])
def test_full_shoe_series_boundaries(size, lengths):
    session = CountingSeriesSession(series_size=size, seed=42)
    seen = Counter()
    for length in lengths:
        assert session.series_length == length
        assert session.shoe_number == 1
        while session.phase == 'showing':
            seen[session.card] += 1
            session.advance()
        assert session.card is None
        session.submit(str(session.running_count))
        if session.shoe.remaining:
            assert session.start_series()
    assert len(seen) == 52 and set(seen.values()) == {6}
    assert session.running_count == 0
    assert session.answered == session.correct == len(lengths)
    assert session.checked_cards == session.total_cards_shown == 312
    assert session.shoe.remaining == 0
    assert session.start_series()
    assert session.shoe_number == 2 and session.shoe.remaining == 311
    assert session.running_count == hi_lo_value(session.card)
    assert session.correct == len(lengths)


def test_card_stays_visible_until_final_advance():
    s = CountingSeriesSession(series_size=2, seed=1)
    assert s.shown_in_series == 1 and s.shoe.position == 1
    with pytest.raises(ValueError):
        s.submit('0')
    assert not s.start_series()
    assert s.advance() and s.phase == 'showing' and s.card is not None
    count = s.running_count
    assert s.advance() and s.phase == 'answer' and s.card is None
    assert s.shoe.position == 2 and s.running_count == count
    assert not s.advance() and not s.start_series()


@pytest.mark.parametrize('answer', ['', ' ', '1.5', 'foo', '++1', '1 2', '1000001'])
def test_invalid_input_does_not_score_or_draw(answer):
    s = CountingSeriesSession(series_size=3)
    finish(s)
    before = (s.running_count, s.shoe.position, s.total_cards_shown)
    with pytest.raises(ValueError):
        s.submit(answer)
    assert s.phase == 'answer' and s.feedback is None
    assert s.answered == s.checked_cards == 0
    assert before == (s.running_count, s.shoe.position, s.total_cards_shown)


def test_stats_streak_error_and_cumulative_count():
    s = CountingSeriesSession(series_size=2, seed=7)
    for error in (0, 0, 3, -1):
        finish(s)
        expected = s.running_count
        s.submit(str(expected + error))
        assert s.running_count == expected
        with pytest.raises(ValueError):
            s.submit(str(expected))
        s.start_series()
        assert s.running_count == expected + hi_lo_value(s.card)
    assert (s.answered, s.correct, s.incorrect) == (4, 2, 2)
    assert s.accuracy == 50 and s.mean_absolute_error == 1
    assert s.streak == 0 and s.best_streak == 2
    assert s.checked_cards == 8 and s.total_cards_shown == 9


def test_limit_does_not_reshuffle_or_draw():
    s = CountingSeriesSession(series_size=500, round_limit=1)
    finish(s)
    s.submit(' +0 ')
    assert s.completed and not s.start_series() and not s.advance()
    assert s.shoe.remaining == 0 and s.shoe_number == 1
    assert s.feedback.correct and s.card is None


def test_seed_and_initial_stats():
    a, b = CountingSeriesSession(seed=9), CountingSeriesSession(seed=9)
    assert a.accuracy == a.mean_absolute_error == a.answered == 0
    for _ in range(10):
        assert a.card == b.card and a.running_count == b.running_count
        a.advance()
        b.advance()


@pytest.mark.parametrize('field,value', [('series_size', 0), ('series_size', -1),
    ('series_size', True), ('series_size', 2.5), ('series_size', None),
    ('round_limit', 0), ('round_limit', False), ('round_limit', 1.5)])
def test_invalid_configuration(field, value):
    with pytest.raises((TypeError, ValueError)):
        CountingSeriesSession(**{field: value})


def test_used_shoe_rejected():
    shoe = Shoe()
    shoe.draw()
    with pytest.raises(ValueError):
        CountingSeriesSession(shoe=shoe)


@pytest.mark.parametrize('flags,size', [([], 10), (['-n','3'], 3), (['--series-size','20'], 20)])
def test_entrypoint(monkeypatch, flags, size):
    import sys
    from blackjack_trainer.__main__ import main
    launch = Mock()
    monkeypatch.setitem(sys.modules, 'blackjack_trainer.counting_series_gui',
                        SimpleNamespace(launch_counting_series_gui=launch))
    monkeypatch.setattr(sys, 'argv', ['trainer', 'count-series', *flags, '--seed','5','--rounds','2'])
    main()
    launch.assert_called_once_with(seed=5, round_limit=2, series_size=size)


@pytest.mark.parametrize('args', [['count-series','-n','0'], ['count-series','-n','-1'],
    ['count-series','-n','1.5'], ['count','-n','10'], ['gui','-n','10']])
def test_invalid_cli_args(monkeypatch, args):
    import sys
    from blackjack_trainer.__main__ import main
    monkeypatch.setattr(sys, 'argv', ['trainer', *args])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_gui_callbacks_hiding_and_cancel(monkeypatch):
    pytest.importorskip('tkinter')
    import blackjack_trainer.counting_series_gui as gui
    app = gui.CountingSeriesApp.__new__(gui.CountingSeriesApp)
    app.session = CountingSeriesSession(series_size=2)
    app._closing = False
    for name in ('card','progress','stats','entry','check','answer_label','message',
                 'next_button','answer','root'):
        setattr(app, name, Mock())
    app.refresh()
    assert app.card.show.call_args.args[0] is app.session.card
    app.on_enter()  # Cannot accidentally answer while viewing cards.
    assert app.session.answered == 0
    app.on_space()
    assert app.session.shown_in_series == 2
    app.on_space()
    app.card.show.assert_called_with(None)
    assert app.session.phase == 'answer'
    app.on_space()
    assert app.session.shoe.position == 2
    app.answer.get.return_value = str(app.session.running_count)
    app.on_enter()
    assert app.session.answered == 1
    app.on_check()
    assert app.session.answered == 1
    monkeypatch.setattr(gui.messagebox, 'askokcancel', lambda *a, **k: False)
    app.on_close()
    app.root.destroy.assert_not_called()
    assert app.session.phase == 'feedback'
    app.on_enter()
    assert app.session.shoe.position == 3
    assert app.session.phase == 'showing'


def test_real_window_smoke():
    tk = pytest.importorskip('tkinter')
    from blackjack_trainer.counting_series_gui import CountingSeriesApp
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('No graphical display available')
    try:
        app = CountingSeriesApp(root, CountingSeriesSession(series_size=1, round_limit=1))
        root.update()
        app.on_space()
        root.update()
        assert app.card._card is None
        app.answer.set(str(app.session.running_count))
        app.on_enter()
        root.update()
        assert app.session.completed
    finally:
        root.destroy()
