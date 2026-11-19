import random
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from blackjack_trainer.step_timer import StepTimer, validate_intervals


class Scheduler:
    def __init__(self):
        self.pending = {}
        self.delays = []
        self.serial = 0

    def after(self, delay, callback):
        self.serial += 1
        self.pending[self.serial] = callback
        self.delays.append(delay)
        return self.serial

    def after_cancel(self, token):
        self.pending.pop(token, None)

    def fire(self):
        assert len(self.pending) == 1
        token = next(iter(self.pending))
        self.pending.pop(token)()


def test_random_delay_for_each_step():
    scheduler = Scheduler()
    step = Mock(return_value=True)
    rng = Mock()
    rng.uniform.side_effect = [0.5, 3.0, 1.25, 2.75]
    timer = StepTimer(scheduler, step, 0.5, 3.0, rng=rng)
    timer.start()
    timer.start()
    for _ in range(3):
        scheduler.fire()
    assert scheduler.delays == [500, 3000, 1250, 2750]
    assert step.call_count == 3 and rng.uniform.call_count == 4
    rng.uniform.assert_called_with(0.5, 3.0)
    assert len(scheduler.pending) == 1


def test_fixed_delay_and_finish():
    scheduler = Scheduler()
    step = Mock(side_effect=[True,True,False])
    rng = Mock()
    timer = StepTimer(scheduler, step, 1.2, 1.2, rng=rng)
    timer.start()
    for _ in range(3):
        scheduler.fire()
    assert scheduler.delays == [1200]*3
    assert not timer.running and not scheduler.pending
    rng.uniform.assert_not_called()


def test_pause_resume_stale_and_duplicate_callbacks():
    scheduler = Scheduler()
    step = Mock(return_value=True)
    timer = StepTimer(scheduler,step,0.5,3,rng=random.Random(1))
    timer.start()
    stale = next(iter(scheduler.pending.values()))
    timer.pause()
    assert not scheduler.pending
    stale()
    step.assert_not_called()
    timer.start()
    stale()
    step.assert_not_called()
    duplicate = next(iter(scheduler.pending.values()))
    scheduler.fire()
    duplicate()
    assert step.call_count == 1 and len(scheduler.pending) == 1
    timer.close()
    timer.close()
    timer.start()
    duplicate()
    assert timer.closed and not timer.running and not scheduler.pending
    assert step.call_count == 1


def test_error_stops_timer():
    scheduler = Scheduler()
    timer = StepTimer(scheduler, Mock(side_effect=RuntimeError('test')), 1, 1)
    timer.start()
    with pytest.raises(RuntimeError):
        scheduler.fire()
    assert not timer.running and not scheduler.pending


@pytest.mark.parametrize('minimum,maximum', [(None,1),(1,None),(0,1),(-1,1),(2,1),
    (float('nan'),1),(1,float('inf')),(True,1),('1',2),(1,3e9)])
def test_invalid_ranges(minimum,maximum):
    with pytest.raises(ValueError):
        validate_intervals(minimum,maximum)


def test_manual_and_submillisecond():
    validate_intervals(None,None)
    with pytest.raises(ValueError):
        StepTimer(Scheduler(),Mock(),None,None)
    scheduler=Scheduler()
    StepTimer(scheduler,Mock(return_value=False),0.0001,0.0001).start()
    assert scheduler.delays == [1]


@pytest.mark.parametrize('values', [('0.5','3'),('1','1')])
def test_cli_dispatch(monkeypatch,values):
    import sys
    from blackjack_trainer.__main__ import main
    launch=Mock()
    monkeypatch.setitem(sys.modules,'blackjack_trainer.counting_table_gui',
                        SimpleNamespace(launch_counting_table_gui=launch))
    monkeypatch.setattr(sys,'argv',['trainer','count-table','--interval-min',values[0],
                                  '--interval-max',values[1]])
    main()
    launch.assert_called_once_with(seed=None,round_limit=None,players=3,
                                   interval_min=float(values[0]),interval_max=float(values[1]))


@pytest.mark.parametrize('args', [
    ['count-table','--interval-min','1'],['count-table','--interval-max','1'],
    ['count-table','--interval-min','2','--interval-max','1'],
    ['count-table','--interval-min','0','--interval-max','1'],
    ['count-table','--interval-min','nan','--interval-max','3'],
    ['count-table','--interval-min','1','--interval-max','inf'],
    ['count-series','--interval-min','1','--interval-max','2'],
])
def test_cli_invalid_ranges(monkeypatch,args):
    import sys
    from blackjack_trainer.__main__ import main
    monkeypatch.setattr(sys,'argv',['trainer',*args])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2


def make_app():
    pytest.importorskip('tkinter')
    from blackjack_trainer.counting_table_gui import CountingTableApp
    from blackjack_trainer.counting_table import CountingTableSession
    app=CountingTableApp.__new__(CountingTableApp)
    app.session=CountingTableSession(players=1,seed=5,round_limit=2)
    app._closing=False
    for name in ('answer','refresh','root','message','next_button'):
        setattr(app,name,Mock())
    scheduler=Scheduler()
    app._timer=StepTimer(scheduler,app._auto_step,0.5,3,rng=random.Random(5))
    app._timer.start()
    return app,scheduler


def test_auto_pause_question_and_next_round():
    app,scheduler=make_app()
    initial=app.session.shoe.position
    app.on_space()
    assert not scheduler.pending and app.session.shoe.position == initial
    app.on_space()
    assert len(scheduler.pending) == 1
    for _ in range(500):
        if not scheduler.pending:
            break
        scheduler.fire()
    assert app.session.phase == 'answer' and not app._timer.running
    assert not app.session.dealer and not any(app.session.players)
    assert app.session.answered == 0
    app.on_space()
    assert not scheduler.pending
    app.answer.get.return_value=str(app.session.running_count)
    app.on_enter()
    assert app.session.answered == 1 and not scheduler.pending
    app.on_enter()
    assert app.session.phase == 'playing' and len(scheduler.pending) == 1
    for _ in range(500):
        if not scheduler.pending:
            break
        scheduler.fire()
    app.answer.get.return_value=str(app.session.running_count)
    app.on_enter()
    app.on_enter()
    assert app.session.completed and not scheduler.pending


@pytest.mark.parametrize('paused', [False,True])
def test_cancel_close_restores_previous_timer_state(monkeypatch,paused):
    import blackjack_trainer.counting_table_gui as gui
    app,scheduler=make_app()
    if paused:
        app.on_space()
    before=app.session.shoe.position
    def cancel(*args,**kwargs):
        assert not scheduler.pending
        app.on_space()
        app.on_enter()
        app.on_next()
        assert app.session.shoe.position == before
        return False
    monkeypatch.setattr(gui.messagebox,'askokcancel',cancel)
    app.on_close()
    assert bool(scheduler.pending) == (not paused)
    assert app._timer.running == (not paused)
    app.root.destroy.assert_not_called()
    assert app.session.shoe.position == before


def test_accept_close_cancels_timer(monkeypatch):
    import blackjack_trainer.counting_table_gui as gui
    app,scheduler=make_app()
    stale=next(iter(scheduler.pending.values()))
    monkeypatch.setattr(gui.messagebox,'askokcancel',lambda *a,**k: True)
    app.on_close()
    stale()
    assert not scheduler.pending and app._timer.closed
    assert app.session.shoe.position == 0
    app.root.destroy.assert_called_once()


def test_timing_does_not_change_shoe():
    from blackjack_trainer.counting_table import CountingTableSession
    app,scheduler=make_app()
    manual=CountingTableSession(players=1,seed=5)
    while manual.phase in ('playing','round_end'):
        manual.advance()
    while scheduler.pending:
        scheduler.fire()
    assert app.session.running_count == manual.running_count
    assert app.session.shoe.cards == manual.shoe.cards
    assert app.session.shoe.position == manual.shoe.position
