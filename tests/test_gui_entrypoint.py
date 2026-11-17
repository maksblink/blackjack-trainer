"""GUI dispatch and graceful errors without requiring Tk or a display."""

import builtins
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from blackjack_trainer import __main__ as entrypoint


def test_gui_options_are_forwarded(monkeypatch):
    launch = Mock()
    monkeypatch.setitem(sys.modules, 'blackjack_trainer.gui', SimpleNamespace(launch_gui=launch))
    monkeypatch.setattr(sys, 'argv', ['blackjack-trainer', 'gui', '--seed', '7', '--rounds', '10'])
    entrypoint.main()
    launch.assert_called_once_with(seed=7, round_limit=10)


def test_missing_tkinter_has_actionable_message(monkeypatch, capsys):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == 'blackjack_trainer.gui':
            raise ModuleNotFoundError('No module named tkinter', name='tkinter')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    monkeypatch.setattr(sys, 'argv', ['blackjack-trainer', 'gui'])
    with pytest.raises(SystemExit) as error:
        entrypoint.main()
    assert error.value.code == 2
    assert 'python -m tkinter' in capsys.readouterr().err


def test_display_error_is_reported_without_traceback(monkeypatch, capsys):
    launch = Mock(side_effect=RuntimeError('Cannot open the GUI.'))
    monkeypatch.setitem(sys.modules, 'blackjack_trainer.gui', SimpleNamespace(launch_gui=launch))
    monkeypatch.setattr(sys, 'argv', ['blackjack-trainer', 'gui'])
    with pytest.raises(SystemExit) as error:
        entrypoint.main()
    assert error.value.code == 2
    assert 'Cannot open the GUI' in capsys.readouterr().err


def test_cli_does_not_import_tkinter():
    script = '''import builtins, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 'tkinter' or name.startswith('tkinter.'):
        raise AssertionError('CLI must not import Tkinter')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
sys.argv = ['blackjack-trainer', 'cli']
from blackjack_trainer.__main__ import main
main()
'''
    result = subprocess.run([sys.executable, '-c', script], input='q\n',
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'SESSION SUMMARY' in result.stdout
