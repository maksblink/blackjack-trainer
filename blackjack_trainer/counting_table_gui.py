"""A scrollable table view for manual, stepwise Hi-Lo practice."""

import tkinter as tk
from tkinter import messagebox, ttk

from blackjack_trainer.counting_table import CountingTableSession
from blackjack_trainer.gui import BG, TABLE, TEXT, MUTED, ACCENT, CardCanvas
from blackjack_trainer.hands import evaluate_hand


class TableCard(CardCanvas):
    def __init__(self, parent, card):
        self._face_down = card is None
        super().__init__(parent)
        self.configure(width=90, height=150)
        self.show(card)

    def _redraw(self):
        if not self._face_down:
            super()._redraw()
            return
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        if width <= 1 or height <= 1:
            width, height = self.BASE_WIDTH, self.BASE_HEIGHT
        scale = min(width / self.BASE_WIDTH, height / self.BASE_HEIGHT) * self.CARD_SCALE
        x, y = (width - self.BASE_WIDTH * scale) / 2, (height - self.BASE_HEIGHT * scale) / 2
        self.create_rectangle(x + 5*scale, y + 5*scale, x + 121*scale, y + 175*scale,
                              fill='#284e78', outline='#ddd9cd', width=max(1, 2*scale))
        self.create_text(x + 63*scale, y + 90*scale, text='?', fill=TEXT,
                         font=('TkDefaultFont', -max(1, round(40*scale)), 'bold'))


class CountingTableApp:
    def __init__(self, root, session):
        self.root, self.session = root, session
        self._closing = False
        root.title('Blackjack Trainer — Hi-Lo Table')
        root.minsize(900, 720)
        root.configure(bg=BG)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        main = tk.Frame(root, bg=BG, padx=18, pady=14)
        main.grid(sticky='nsew')
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        tk.Label(main, text='HI-LO TABLE TRAINER', bg=BG, fg=ACCENT,
                 font=('TkDefaultFont', 22, 'bold')).grid(row=0, sticky='w')
        tk.Label(main, text='H17 · DAS · Dealer peek · Up to 4 hands per player · No surrender',
                 bg=BG, fg=MUTED).grid(row=1, sticky='w', pady=6)
        self.progress = tk.StringVar(root)
        tk.Label(main, textvariable=self.progress, bg=BG, fg=MUTED).grid(row=2, sticky='w')
        area = tk.Frame(main, bg=TABLE)
        area.grid(row=3, sticky='nsew', pady=10)
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.viewport = tk.Canvas(area, bg=TABLE, highlightthickness=0)
        self.viewport.grid(sticky='nsew')
        scroll = ttk.Scrollbar(area, orient='vertical', command=self.viewport.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.viewport.configure(yscrollcommand=scroll.set)
        self.table = tk.Frame(self.viewport, bg=TABLE)
        self.table_window = self.viewport.create_window(0, 0, window=self.table, anchor='nw')
        self.table.bind('<Configure>', lambda e: self.viewport.configure(scrollregion=self.viewport.bbox('all')))
        self.viewport.bind('<Configure>', lambda e: self.viewport.itemconfigure(self.table_window, width=e.width))
        self.message = tk.StringVar(root)
        tk.Label(main, textvariable=self.message, bg=BG, fg=TEXT, wraplength=840,
                 justify='left').grid(row=4, sticky='w', pady=6)
        self.controls = tk.Frame(main, bg=BG)
        self.controls.grid(row=5, sticky='ew')
        self.answer_label = tk.Label(self.controls, text='Running count:', bg=BG, fg=TEXT)
        self.answer = tk.StringVar(root)
        self.entry = ttk.Entry(self.controls, textvariable=self.answer, width=12)
        self.check = ttk.Button(self.controls, text='Check', command=self.on_check)
        self.next_button = ttk.Button(self.controls, text='Next step', command=self.on_next)
        self.next_button.pack(side='left', padx=8)
        self.quit_button = ttk.Button(self.controls, text='Quit', command=self.on_close)
        self.quit_button.pack(side='right')
        self.stats = tk.StringVar(root)
        tk.Label(main, textvariable=self.stats, bg=BG, fg=MUTED, justify='left').grid(row=6, sticky='w', pady=8)
        tk.Label(main, text='Space: next step / hide table · Enter: check / next round · Esc: quit',
                 bg=BG, fg=MUTED).grid(row=7, sticky='w')
        for widget in (root, self.entry, self.check, self.next_button, self.quit_button):
            widget.bind('<space>', self.on_space)
            widget.bind('<Return>', self.on_enter)
            widget.bind('<KP_Enter>', self.on_enter)
            widget.bind('<Escape>', self.on_escape)
        root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.refresh()

    def statistics_text(self):
        s = self.session
        return (f'Rounds checked: {s.answered} · Correct: {s.correct} · Incorrect: {s.incorrect} '
                f'· Accuracy: {s.accuracy:.1f}%\n'
                f'Streak: {s.streak} · Best: {s.best_streak} · Mean absolute error: {s.mean_absolute_error:.2f}\n'
                f'Cards checked: {s.checked_cards} · Cards seen: {s.total_cards_seen}')

    def _hand_view(self, parent, cards, label, from_split=False):
        tk.Label(parent, text=label, bg=TABLE, fg=TEXT,
                 font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        strip = tk.Frame(parent, bg=TABLE, height=160)
        strip.pack(fill='x')
        for i, card in enumerate(cards):
            strip.columnconfigure(i, weight=1, uniform='cards')
            TableCard(strip, card).grid(row=0, column=i, sticky='nsew')
        if cards and all(card is not None for card in cards):
            hand = evaluate_hand(cards, from_split=from_split)
            value = 'Blackjack' if hand.is_blackjack else 'Bust' if hand.is_bust else 'Soft' if hand.is_soft else 'Hard'
            tk.Label(parent, text=f'{value} {hand.total}', bg=TABLE, fg=MUTED).pack(anchor='w')

    def render_table(self):
        position = self.viewport.yview()[0]
        for widget in self.table.winfo_children():
            widget.destroy()
        s = self.session
        if s.phase in ('answer', 'feedback'):
            tk.Label(self.table, text='Table hidden', bg=TABLE, fg=MUTED,
                     font=('TkDefaultFont', 18)).grid(padx=30, pady=60)
            return
        columns = min(3, s.player_count)
        for col in range(3):
            self.table.columnconfigure(col, weight=1, uniform='seats')
        dealer = tk.Frame(self.table, bg=TABLE, padx=8, pady=8)
        dealer.grid(row=0, column=1, sticky='nsew')
        self._hand_view(dealer, s.dealer, 'DEALER')
        for p, hands in enumerate(s.players):
            seat = tk.Frame(self.table, bg=TABLE, padx=8, pady=8,
                            highlightbackground='#427562', highlightthickness=1)
            seat.grid(row=1 + p // columns, column=p % columns, sticky='nsew', padx=4, pady=4,
                      columnspan=3 if columns == 1 else 1)
            for h, hand in enumerate(hands):
                label = f'PLAYER {p+1} · HAND {h+1}' + (f' · {hand.status}' if hand.status else '')
                self._hand_view(seat, hand.cards, label, hand.from_split)
        self.viewport.yview_moveto(position)

    def refresh(self):
        s = self.session
        self.render_table()
        self.progress.set(f'Shoe {s.shoe_number} · Round {s.answered + (s.phase != "feedback")} '
                          f'· Cards remaining: {s.shoe.remaining}')
        self.stats.set(self.statistics_text())
        for widget in (self.answer_label, self.entry, self.check):
            widget.pack_forget()
        self.message.set(s.message)
        if s.phase == 'answer':
            self.answer_label.pack(side='left', before=self.next_button)
            self.entry.pack(side='left', padx=8, before=self.next_button)
            self.check.pack(side='left', before=self.next_button)
            self.next_button.state(['disabled'])
            self.entry.focus_set()
        elif s.phase == 'feedback':
            f = s.feedback
            verdict = 'Correct!' if f.correct else f'Incorrect — you entered {f.chosen:+d}.'
            self.message.set(f'{verdict} Running count: {f.expected:+d}.' +
                             (' Session complete.' if s.completed else ' Continue from this count.'))
            self.next_button.configure(text='Next round')
            self.next_button.state(['disabled' if s.completed else '!disabled'])
            if not s.completed:
                self.next_button.focus_set()
        else:
            self.next_button.configure(text='Hide table and answer' if s.phase == 'round_end' else 'Next step')
            self.next_button.state(['!disabled'])
            self.next_button.focus_set()

    def on_next(self):
        if self._closing:
            return
        changed = self.session.start_round() if self.session.phase == 'feedback' else self.session.advance()
        if changed:
            self.answer.set('')
            self.refresh()

    def on_check(self):
        if self._closing or self.session.phase != 'answer':
            return
        try:
            self.session.submit(self.answer.get())
        except ValueError as error:
            self.message.set(str(error))
            return
        self.refresh()

    def on_space(self, _event=None):
        if self.session.phase in ('playing', 'round_end'):
            self.on_next()
        return 'break'

    def on_enter(self, _event=None):
        if self.session.phase == 'answer':
            self.on_check()
        elif self.session.phase == 'feedback':
            self.on_next()
        return 'break'

    def on_escape(self, _event=None):
        self.on_close()
        return 'break'

    def on_close(self):
        if self._closing:
            return
        self._closing = True
        try:
            if messagebox.askokcancel('End session', self.statistics_text() + '\n\nClose the trainer?', parent=self.root):
                self.root.destroy()
        finally:
            self._closing = False


def launch_counting_table_gui(*, players=3, seed=None, round_limit=None):
    session = CountingTableSession(players=players, seed=seed, round_limit=round_limit)
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError('Cannot open the GUI. Use a graphical desktop with working Tcl/Tk.') from error
    try:
        CountingTableApp(root, session)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
