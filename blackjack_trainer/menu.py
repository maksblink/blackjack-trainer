"""Training launcher with one Tk event loop and a child training window."""

import tkinter as tk
from tkinter import ttk

from blackjack_trainer.gui import BG, TEXT, MUTED, ACCENT
from blackjack_trainer.menu_config import MODES, parse_menu_config


def build_training_window(window, config):
    """Reuse each trainer's UI and session without starting nested main loops."""
    if config.mode == 'gui':
        from blackjack_trainer.gui import StrategyApp
        from blackjack_trainer.gui_controller import StrategyController
        from blackjack_trainer.training import StrategySession
        return StrategyApp(window, StrategyController(
            StrategySession(seed=config.seed), round_limit=config.round_limit))
    if config.mode == 'count':
        from blackjack_trainer.counting import CountingSession
        from blackjack_trainer.counting_gui import CountingApp
        return CountingApp(window, CountingSession(seed=config.seed, round_limit=config.round_limit))
    if config.mode == 'count-series':
        from blackjack_trainer.counting_series import CountingSeriesSession
        from blackjack_trainer.counting_series_gui import CountingSeriesApp
        return CountingSeriesApp(window, CountingSeriesSession(
            seed=config.seed, round_limit=config.round_limit, series_size=config.series_size))
    if config.mode == 'count-table':
        from blackjack_trainer.counting_table import CountingTableSession
        from blackjack_trainer.counting_table_gui import CountingTableApp
        return CountingTableApp(window, CountingTableSession(
            seed=config.seed, round_limit=config.round_limit, players=config.players),
            interval_min=config.interval_min, interval_max=config.interval_max, seed=config.seed)
    raise ValueError('Unknown training mode.')


class LauncherApp:
    def __init__(self, root, *, seed=None, round_limit=None):
        self.root = root
        self.child = None
        self.trainer = None
        root.title('Blackjack Trainer')
        root.minsize(640, 590)
        root.configure(bg=BG)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main = tk.Frame(root, bg=BG, padx=28, pady=24)
        main.grid(sticky='nsew')
        main.columnconfigure(1, weight=1)
        tk.Label(main, text='BLACKJACK TRAINER', bg=BG, fg=ACCENT,
                 font=('TkDefaultFont', 22, 'bold')).grid(row=0, columnspan=2, sticky='w')
        tk.Label(main, text='Choose a mode and start practicing.', bg=BG, fg=MUTED).grid(
            row=1, columnspan=2, sticky='w', pady=(6, 18))
        self.mode = tk.StringVar(root, value='Basic strategy')
        self.rounds = tk.StringVar(root, value='' if round_limit is None else str(round_limit))
        self.seed = tk.StringVar(root, value='' if seed is None else str(seed))
        self.series_size = tk.StringVar(root, value='10')
        self.players = tk.StringVar(root, value='3')
        self.automatic = tk.BooleanVar(root, value=False)
        self.interval_min = tk.StringVar(root, value='0.5')
        self.interval_max = tk.StringVar(root, value='3')
        self.error = tk.StringVar(root)
        self.description = tk.StringVar(root)
        tk.Label(main, text='Training mode', bg=BG, fg=TEXT).grid(row=2, column=0, sticky='w')
        self.mode_box = ttk.Combobox(main, textvariable=self.mode, values=list(MODES), state='readonly')
        self.mode_box.grid(row=2, column=1, sticky='ew', padx=(16, 0), pady=6)
        self.mode_box.bind('<<ComboboxSelected>>', self.update_fields)
        tk.Label(main, textvariable=self.description, bg=BG, fg=MUTED,
                 wraplength=550, justify='left').grid(row=3, columnspan=2, sticky='w', pady=10)

        def entry(row, label, variable):
            tk.Label(main, text=label, bg=BG, fg=TEXT).grid(row=row, column=0, sticky='w')
            widget = ttk.Entry(main, textvariable=variable)
            widget.grid(row=row, column=1, sticky='ew', padx=(16, 0), pady=6)
            return widget

        entry(4, 'Question limit (blank = unlimited)', self.rounds)
        entry(5, 'Seed (optional)', self.seed)
        self.series_entry = entry(6, 'Cards per series', self.series_size)
        self.players_entry = entry(7, 'Players (1–7)', self.players)
        self.auto_check = ttk.Checkbutton(main, text='Automatic table tempo', variable=self.automatic,
                                          command=self.update_fields)
        self.auto_check.grid(row=8, columnspan=2, sticky='w', pady=8)
        self.minimum_entry = entry(9, 'Minimum delay (seconds)', self.interval_min)
        self.maximum_entry = entry(10, 'Maximum delay (seconds)', self.interval_max)
        tk.Label(main, textvariable=self.error, bg=BG, fg='#ffbaa9', wraplength=550,
                 justify='left').grid(row=11, columnspan=2, sticky='w', pady=10)
        footer = tk.Frame(main, bg=BG)
        footer.grid(row=12, columnspan=2, sticky='ew')
        self.start_button = ttk.Button(footer, text='Start', command=self.on_start)
        self.start_button.pack(side='left')
        ttk.Button(footer, text='Quit', command=root.destroy).pack(side='right')
        root.bind('<Return>', self.on_start)
        root.bind('<KP_Enter>', self.on_start)
        self.update_fields()
        self.mode_box.focus_set()

    def update_fields(self, _event=None):
        mode = MODES.get(self.mode.get())
        series, table = mode == 'count-series', mode == 'count-table'
        self.series_entry.configure(state='normal' if series else 'disabled')
        self.players_entry.configure(state='normal' if table else 'disabled')
        self.auto_check.state(['!disabled' if table else 'disabled'])
        timed = table and self.automatic.get()
        for widget in (self.minimum_entry, self.maximum_entry):
            widget.configure(state='normal' if timed else 'disabled')
        self.description.set({
            'gui': 'Choose the best opening action. The limit counts answered hands.',
            'count': 'Enter the running count after each card. The limit counts answered cards.',
            'count-series': 'Remember a series of cards, then enter the count. The limit counts answered series.',
            'count-table': 'Watch a full round, then enter the count. The limit counts answered rounds.',
        }.get(mode, 'Choose a training mode.'))
        self.error.set('')

    def on_start(self, _event=None):
        if self.child is not None:
            return 'break'
        try:
            config = parse_menu_config(
                mode=self.mode.get(), rounds=self.rounds.get(), seed=self.seed.get(),
                series_size=self.series_size.get(), players=self.players.get(),
                automatic=self.automatic.get(), interval_min=self.interval_min.get(),
                interval_max=self.interval_max.get())
        except ValueError as error:
            self.error.set(str(error))
            return 'break'
        self.error.set('')
        self.start_button.state(['disabled'])
        child = tk.Toplevel(self.root)
        self.child = child
        child.withdraw()
        child.bind('<Destroy>', self._child_destroyed, add='+')
        try:
            self.trainer = build_training_window(child, config)
        except (RuntimeError, ValueError, OSError, tk.TclError) as error:
            child.destroy()
            self.error.set(f'Cannot start training: {error}')
            return 'break'
        self.root.withdraw()
        child.deiconify()
        child.lift()
        return 'break'

    def _child_destroyed(self, event):
        if event.widget is not self.child:
            return
        timer = getattr(self.trainer, '_timer', None)
        if timer is not None:
            timer.close()
        self.child = self.trainer = None
        self.root.after_idle(self._return_to_menu)

    def _return_to_menu(self):
        if self.child is None and self.root.winfo_exists():
            self.root.deiconify()
            self.root.lift()
            self.start_button.state(['!disabled'])
            self.start_button.focus_set()


def launch_menu(*, seed=None, round_limit=None):
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError('Cannot open the GUI. Use a graphical desktop with working Tcl/Tk.') from error
    app = None
    try:
        app = LauncherApp(root, seed=seed, round_limit=round_limit)
        root.mainloop()
    finally:
        timer = getattr(getattr(app, 'trainer', None), '_timer', None)
        if timer is not None:
            timer.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
