"""Window callbacks plus an optional smoke test against a real Tk display."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

tk = pytest.importorskip('tkinter')
from blackjack_trainer.gui import StrategyApp
from blackjack_trainer.gui_controller import StrategyController
from blackjack_trainer.shoe import Shoe
from blackjack_trainer.training import StrategySession


@pytest.fixture
def app():
    instance = StrategyApp.__new__(StrategyApp)
    instance.root = Mock()
    instance.controller = StrategyController(StrategySession(shoe=Shoe(shuffle=False)))
    instance._closing_dialog = False
    instance.refresh = Mock()
    return instance


def test_cancel_quit_does_not_destroy_window(app, monkeypatch):
    monkeypatch.setattr('blackjack_trainer.gui.messagebox.askokcancel', lambda *a, **k: False)
    app.on_close()
    app.root.destroy.assert_not_called()
    assert app.controller.can_answer
    assert app.controller.session.shoe.position == 3
    assert not app._closing_dialog


def test_confirm_quit_destroys_window(app, monkeypatch):
    monkeypatch.setattr('blackjack_trainer.gui.messagebox.askokcancel', lambda *a, **k: True)
    app.on_close()
    app.root.destroy.assert_called_once()
    assert app.controller.closed


@pytest.mark.parametrize('key', ['h', 'H', 's', 'd', 'p'])
def test_answer_shortcuts(app, key):
    assert app.on_key(SimpleNamespace(keysym=key)) == 'break'
    assert app.controller.session.answered == 1
    app.refresh.assert_called_once()


@pytest.mark.parametrize('key', ['Return', 'KP_Enter', 'space'])
def test_next_shortcuts_are_guarded(app, key):
    app.on_key(SimpleNamespace(keysym=key))
    assert app.controller.session.shoe.position == 3
    app.on_key(SimpleNamespace(keysym='h'))
    app.on_key(SimpleNamespace(keysym=key))
    assert app.controller.session.shoe.position == 6
    app.on_key(SimpleNamespace(keysym=key))
    assert app.controller.session.shoe.position == 6


def test_unrelated_key_is_ignored(app):
    assert app.on_key(SimpleNamespace(keysym='x')) is None
    assert app.controller.session.answered == 0


def test_dialog_blocks_answers_and_next(app):
    app._closing_dialog = True
    app.on_key(SimpleNamespace(keysym='h'))
    app.on_key(SimpleNamespace(keysym='Return'))
    assert app.controller.session.answered == 0
    app.refresh.assert_not_called()


def test_real_window_smoke(monkeypatch):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('No graphical display available for the Tk window smoke test')
    root.withdraw()
    try:
        window = StrategyApp(root, StrategyController(StrategySession(shoe=Shoe(shuffle=False))))
        root.update_idletasks()
        assert len(window.player_cards[0].find_all()) > 0
        assert window.next_button.instate(['disabled'])
        window.on_key(SimpleNamespace(keysym='h'))
        assert 'Correct!' in window.feedback_var.get()
        assert window.next_button.instate(['!disabled'])
        assert all(button.instate(['disabled']) for button in window.action_buttons.values())
        window.on_next()
        assert window.controller.session.shoe.position == 6
        monkeypatch.setattr('blackjack_trainer.gui.messagebox.askokcancel', lambda *a, **k: False)
        window.on_close()
        assert root.winfo_exists()
    finally:
        root.destroy()
