"""Desktop Hi-Lo trainer using the shared card renderer."""

import tkinter as tk
from tkinter import messagebox, ttk

from blackjack_trainer.counting import CountingSession
from blackjack_trainer.gui import BG, TABLE, TEXT, MUTED, ACCENT, CardCanvas


class CountingApp:
    def __init__(self, root: tk.Tk, session: CountingSession) -> None:
        self.root = root
        self.session = session
        self._closing = False
        root.title('Blackjack Trainer — Hi-Lo')
        root.minsize(620, 640)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.on_close)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame = tk.Frame(root, bg=BG, padx=24, pady=20)
        frame.grid(sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)
        tk.Label(frame, text='HI-LO COUNTING TRAINER', bg=BG, fg=ACCENT,
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
        tk.Label(controls, text='Running count:', bg=BG, fg=TEXT).pack(side='left')
        self.answer = tk.StringVar(root)
        self.entry = ttk.Entry(controls, textvariable=self.answer, width=12)
        self.entry.pack(side='left', padx=10)
        self.check = ttk.Button(controls, text='Check', command=self.on_check)
        self.check.pack(side='left')
        self.next_button = ttk.Button(controls, text='Next card', command=self.on_next)
        self.next_button.pack(side='left', padx=10)
        self.stats = tk.StringVar(root)
        tk.Label(frame, textvariable=self.stats, bg=BG, fg=MUTED).grid(row=6, sticky='w', pady=12)
        ttk.Button(frame, text='Quit', command=self.on_close).grid(row=7, sticky='e')
        tk.Label(frame, text='Enter: check / next card  ·  Esc: quit',
                 bg=BG, fg=MUTED).grid(row=8, sticky='w')
        root.bind('<Return>', self.on_enter)
        root.bind('<KP_Enter>', self.on_enter)
        root.bind('<Escape>', self.on_escape)
        self.refresh()

    def refresh(self) -> None:
        session = self.session
        self.card.show(session.card)
        self.progress.set(f'Shoe {session.shoe_number} · Cards shown: {session.shoe.position} '
                          f'· Cards remaining: {session.shoe.remaining}')
        self.stats.set(f'Answered: {session.answered} · Correct: {session.correct} '
                       f'· Accuracy: {session.accuracy:.1f}%')
        feedback = session.feedback
        if feedback is None:
            prompt = 'What is the running count after this card?'
            if session.shoe.position == 1:
                prompt = 'New shoe: start from 0. ' + prompt
            self.message.set(prompt)
        else:
            verdict = 'Correct!' if feedback.correct else f'Incorrect — you entered {feedback.chosen:+d}.'
            self.message.set(f'{verdict} Running count: {feedback.expected:+d}.'
                             + (' Session complete.' if session.completed else ' Continue from this count.'))
        can_answer = feedback is None and not session.completed
        self.entry.configure(state='normal' if can_answer else 'disabled')
        self.check.state(['!disabled' if can_answer else 'disabled'])
        self.next_button.state(['!disabled' if feedback is not None and not session.completed else 'disabled'])
        if can_answer:
            self.entry.focus_set()
        elif not session.completed:
            self.next_button.focus_set()

    def on_check(self) -> None:
        if self._closing or self.session.feedback is not None or self.session.completed:
            return
        try:
            self.session.submit(self.answer.get())
        except ValueError as error:
            self.message.set(str(error))
            return
        self.refresh()

    def on_next(self) -> None:
        if not self._closing and self.session.next_card():
            self.answer.set('')
            self.refresh()

    def on_enter(self, _event=None) -> str:
        if self.session.feedback is None:
            self.on_check()
        else:
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
            session = self.session
            if messagebox.askokcancel('End session',
                    f'Answered: {session.answered}\nCorrect: {session.correct}\n'
                    f'Accuracy: {session.accuracy:.1f}%\n\nClose the trainer?', parent=self.root):
                self.root.destroy()
        finally:
            self._closing = False


def launch_counting_gui(*, seed: int | None = None, round_limit: int | None = None) -> None:
    session = CountingSession(seed=seed, round_limit=round_limit)
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError('Cannot open the GUI. Use a graphical desktop with working Tcl/Tk.') from error
    try:
        CountingApp(root, session)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
