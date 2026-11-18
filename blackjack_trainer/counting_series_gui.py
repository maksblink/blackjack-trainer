"""Desktop Hi-Lo trainer using the shared card renderer."""

import tkinter as tk
from tkinter import messagebox, ttk

from blackjack_trainer.counting_series import CountingSeriesSession
from blackjack_trainer.gui import BG, TABLE, TEXT, MUTED, ACCENT, CardCanvas


class CountingSeriesApp:
    def __init__(self, root: tk.Tk, session: CountingSeriesSession) -> None:
        self.root = root
        self.session = session
        self._closing = False
        root.title('Blackjack Trainer — Hi-Lo Series')
        root.minsize(620, 640)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.on_close)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = tk.Frame(root, bg=BG, padx=24, pady=20)
        frame.grid(sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)
        tk.Label(frame, text='HI-LO SERIES TRAINER', bg=BG, fg=ACCENT,
                 font=('TkDefaultFont', 22, 'bold')).grid(sticky='w')
        tk.Label(frame, text='2–6: +1  ·  7–9: 0  ·  10 / J / Q / K / A: −1',
                 bg=BG, fg=MUTED).grid(row=1, sticky='w', pady=(4, 10))
        self.progress = tk.StringVar(root)
        tk.Label(frame, textvariable=self.progress, bg=BG, fg=MUTED).grid(row=2, sticky='w')
        table = tk.Frame(frame, bg=TABLE)
        table.grid(row=3, sticky='nsew', pady=12)
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.card = CardCanvas(table)
        self.card.grid(sticky='nsew')
        self.message = tk.StringVar(root)
        tk.Label(frame, textvariable=self.message, bg=BG, fg=TEXT,
                 wraplength=560, justify='left').grid(row=4, sticky='w', pady=8)
        controls = tk.Frame(frame, bg=BG)
        controls.grid(row=5, sticky='ew')
        self.answer_label = tk.Label(controls, text='Running count:', bg=BG, fg=TEXT)
        self.answer = tk.StringVar(root)
        self.entry = ttk.Entry(controls, textvariable=self.answer, width=12)
        self.check = ttk.Button(controls, text='Check', command=self.on_check)
        self.next_button = ttk.Button(controls, text='Next card', command=self.on_next)
        self.next_button.pack(side='left', padx=10)
        self.stats = tk.StringVar(root)
        tk.Label(frame, textvariable=self.stats, bg=BG, fg=MUTED).grid(row=6, sticky='w', pady=12)
        self.quit_button = ttk.Button(frame, text='Quit', command=self.on_close)
        self.quit_button.grid(row=7, sticky='e')
        tk.Label(frame, text='Space: next card / finish series  ·  Enter: check / next series  ·  Esc: quit',
                 bg=BG, fg=MUTED).grid(row=8, sticky='w')
        root.bind('<Return>', self.on_enter)
        root.bind('<KP_Enter>', self.on_enter)
        root.bind('<Escape>', self.on_escape)
        # Handle keys before ttk class bindings can activate a focused button.
        for widget in (self.next_button, self.check, self.entry, self.quit_button):
            widget.bind('<space>', self.on_space)
            widget.bind('<Return>', self.on_enter)
            widget.bind('<KP_Enter>', self.on_enter)
        root.bind('<space>', self.on_space)
        self.refresh()

    def statistics_text(self) -> str:
        s = self.session
        return (f'Series checked: {s.answered} · Correct: {s.correct} · Incorrect: {s.incorrect}\n'
                f'Accuracy: {s.accuracy:.1f}% · Streak: {s.streak} · Best: {s.best_streak}\n'
                f'Mean absolute error: {s.mean_absolute_error:.2f} · Cards checked: {s.checked_cards}'
                f' · Cards shown: {s.total_cards_shown}')

    def refresh(self) -> None:
        s = self.session
        # show(None) also clears the renderer's card, so resizing cannot reveal it.
        self.card.show(s.card)
        self.progress.set(f'Shoe {s.shoe_number} · Series {s.answered + (s.phase != "feedback")} '
                          f'· Card {s.shown_in_series} / {s.series_length} '
                          f'· Cards remaining: {s.shoe.remaining}')
        self.stats.set(self.statistics_text())
        for widget in (self.entry, self.check, self.answer_label):
            widget.pack_forget()
        if s.phase == 'showing':
            prefix = 'New shoe: count starts at 0. ' if s.new_shoe and s.shown_in_series == 1 else ''
            prompt = 'Press Space for the next card.' if s.shown_in_series < s.series_length else 'Last card. Press Space to hide it and answer.'
            if s.series_length < s.series_size:
                prefix += f'Short series: only {s.series_length} cards remained in this shoe. '
            self.message.set(prefix + prompt)
            self.next_button.configure(text='Next card' if s.shown_in_series < s.series_length else 'Finish series')
            self.next_button.state(['!disabled'])
            self.next_button.focus_set()
        elif s.phase == 'answer':
            self.message.set('What is the cumulative running count after this series?')
            self.answer_label.pack(side='left', before=self.next_button)
            self.entry.pack(side='left', padx=10, before=self.next_button)
            self.check.pack(side='left', before=self.next_button)
            self.next_button.state(['disabled'])
            self.entry.focus_set()
        else:
            f = s.feedback
            verdict = 'Correct!' if f.correct else f'Incorrect — you entered {f.chosen:+d}.'
            self.message.set(f'{verdict} Running count: {f.expected:+d}.' +
                             (' Session complete.' if s.completed else ' Continue from this count.'))
            self.next_button.configure(text='Next series')
            self.next_button.state(['disabled' if s.completed else '!disabled'])
            if not s.completed:
                self.next_button.focus_set()

    def on_check(self) -> None:
        if self._closing or self.session.phase != 'answer':
            return
        try:
            self.session.submit(self.answer.get())
        except ValueError as error:
            self.message.set(str(error))
            return
        self.refresh()

    def on_next(self) -> None:
        if self._closing:
            return
        s = self.session
        changed = s.advance() if s.phase == 'showing' else s.start_series() if s.phase == 'feedback' else False
        if changed:
            self.answer.set('')
            self.refresh()

    def on_space(self, _event=None) -> str:
        if self.session.phase == 'showing':
            self.on_next()
        return 'break'

    def on_enter(self, _event=None) -> str:
        if self.session.phase == 'answer':
            self.on_check()
        elif self.session.phase == 'feedback':
            self.on_next()
        return 'break'

    def on_escape(self, _event=None) -> str:
        self.on_close()
        return 'break'

    def on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        try:
            if messagebox.askokcancel('End session', self.statistics_text() +
                                     '\n\nClose the trainer?', parent=self.root):
                self.root.destroy()
        finally:
            self._closing = False


def launch_counting_series_gui(*, seed: int | None = None, round_limit: int | None = None,
                               series_size: int = 10) -> None:
    session = CountingSeriesSession(seed=seed, round_limit=round_limit, series_size=series_size)
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError('Cannot open the GUI. Use a graphical desktop with working Tcl/Tk.') from error
    try:
        CountingSeriesApp(root, session)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
