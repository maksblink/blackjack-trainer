from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from blackjack_trainer.menu_config import MODES, parse_menu_config


@pytest.mark.parametrize('label,mode', list(MODES.items()))
def test_defaults(label,mode):
    config=parse_menu_config(mode=label)
    assert config.mode == mode
    assert config.round_limit is config.seed is None
    assert config.series_size == 10 and config.players == 3
    assert config.interval_min is config.interval_max is None


def test_table_settings():
    c=parse_menu_config(mode='Hi-Lo: full table', rounds=' 20 ',seed='-42',players='7',
                        automatic=True,interval_min='0.5',interval_max='3')
    assert (c.round_limit,c.seed,c.players,c.interval_min,c.interval_max)==(20,-42,7,0.5,3)
    fixed=parse_menu_config(mode='Hi-Lo: full table',automatic=True,interval_min='1',interval_max='1')
    assert fixed.interval_min == fixed.interval_max == 1


def test_series_and_ignored_disabled_fields():
    c=parse_menu_config(mode='Hi-Lo: card series',series_size='5',players='bad',automatic=True,
                        interval_min='bad',interval_max='bad')
    assert c.series_size == 5 and c.interval_min is None
    c=parse_menu_config(mode='Hi-Lo: full table',series_size='bad',interval_min='bad')
    assert c.interval_min is None


@pytest.mark.parametrize('fields', [dict(mode='unknown'),dict(rounds='0'),dict(rounds='-1'),
    dict(rounds='2.5'),dict(seed='1.5'),dict(mode='Hi-Lo: card series',series_size='0'),
    dict(mode='Hi-Lo: full table',players='8'),dict(mode='Hi-Lo: full table',players='0'),
    dict(mode='Hi-Lo: full table',automatic=True,interval_min='nan'),
    dict(mode='Hi-Lo: full table',automatic=True,interval_min='4',interval_max='3'),
    dict(mode='Hi-Lo: full table',automatic=True,interval_min='0'),
    dict(mode='Hi-Lo: full table',automatic=True,interval_max=''),
])
def test_invalid_fields(fields):
    values=dict(mode='Basic strategy')
    values.update(fields)
    with pytest.raises(ValueError):
        parse_menu_config(**values)


def test_cli_dispatch(monkeypatch):
    import sys
    from blackjack_trainer.__main__ import main
    launch=Mock()
    monkeypatch.setitem(sys.modules,'blackjack_trainer.menu',SimpleNamespace(launch_menu=launch))
    monkeypatch.setattr(sys,'argv',['trainer','menu','--seed','4','--rounds','12'])
    main()
    launch.assert_called_once_with(seed=4,round_limit=12)


def test_validation_does_not_open_window(monkeypatch):
    pytest.importorskip('tkinter')
    import blackjack_trainer.menu as menu
    app=menu.LauncherApp.__new__(menu.LauncherApp)
    app.child=None
    for name,value in dict(mode='Basic strategy',rounds='bad',seed='',series_size='10',players='3',
                           automatic=False,interval_min='0.5',interval_max='3').items():
        setattr(app,name,Mock(get=Mock(return_value=value)))
    app.error=Mock()
    top=Mock()
    monkeypatch.setattr(menu.tk,'Toplevel',top)
    assert app.on_start()=='break'
    top.assert_not_called()
    assert 'whole number' in app.error.set.call_args.args[0]


def test_double_start_guard():
    pytest.importorskip('tkinter')
    from blackjack_trainer.menu import LauncherApp
    app=LauncherApp.__new__(LauncherApp)
    app.child=object()
    assert app.on_start()=='break'


def test_destroy_filter_and_timer_cleanup():
    pytest.importorskip('tkinter')
    from blackjack_trainer.menu import LauncherApp
    app=LauncherApp.__new__(LauncherApp)
    app.root=Mock()
    app.child=object()
    timer=Mock()
    app.trainer=SimpleNamespace(_timer=timer)
    app._child_destroyed(SimpleNamespace(widget=object()))
    timer.close.assert_not_called()
    child=app.child
    app._child_destroyed(SimpleNamespace(widget=child))
    timer.close.assert_called_once()
    assert app.child is app.trainer is None
    app.root.after_idle.assert_called_once()


@pytest.mark.parametrize('mode', list(MODES))
def test_real_menu_launch_and_return(mode,monkeypatch):
    tk=pytest.importorskip('tkinter')
    from blackjack_trainer.menu import LauncherApp
    try:
        root=tk.Tk()
    except tk.TclError:
        pytest.skip('No graphical display available')
    try:
        app=LauncherApp(root)
        app.mode.set(mode)
        app.rounds.set('1')
        if mode=='Hi-Lo: full table':
            app.automatic.set(True)
            app.interval_min.set('10')
            app.interval_max.set('10')
        app.update_fields()
        root.update()
        app.on_start()
        root.update()
        assert app.child is not None and root.state()=='withdrawn'
        trainer=app.trainer
        timer=getattr(trainer,'_timer',None)
        monkeypatch.setattr('tkinter.messagebox.askokcancel', lambda *a,**k:False)
        trainer.on_close()
        root.update()
        assert app.child is not None
        monkeypatch.setattr('tkinter.messagebox.askokcancel', lambda *a,**k:True)
        trainer.on_close()
        root.update()
        assert app.child is app.trainer is None
        assert root.state()=='normal' and app.mode.get()==mode
        if timer is not None:
            assert timer.closed and not timer.running
        # A second launch creates a fresh session and can return again.
        app.on_start()
        root.update()
        assert app.trainer is not trainer
        app.trainer.on_close()
        root.update()
        assert app.child is None
    finally:
        root.destroy()
