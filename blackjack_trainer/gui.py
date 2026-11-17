"""Tkinter desktop interface for opening-decision practice."""

import tkinter as tk
from tkinter import messagebox, ttk

from blackjack_trainer.cards import Card
from blackjack_trainer.gui_controller import StrategyController
from blackjack_trainer.hands import evaluate_hand
from blackjack_trainer.strategy import Action
from blackjack_trainer.training import StrategySession

BG = "#101b20"
PANEL = "#18292f"
TABLE = "#124c3c"
TEXT = "#f0f4ef"
MUTED = "#b0c7be"
ACCENT = "#efcd7a"


class CardCanvas(tk.Canvas):
    """Draw a card using Tk primitives, without external images or fonts."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, width=130, height=184, bg=TABLE,
                         highlightthickness=0, borderwidth=0)

    def show(self, card: Card) -> None:
        self.delete("all")
        self.create_rectangle(10, 10, 126, 180, fill="#09382c", outline="")
        self.create_rectangle(5, 5, 121, 175, fill="#faf8f0", outline="#ddd9cd", width=2)
        color = "#b33142" if card.suit in ("♥", "♦") else "#1b2b31"
        self.create_text(18, 20, text=card.rank, anchor="nw", fill=color,
                         font=("TkDefaultFont", 18, "bold"))
        self.create_text(20, 49, text=card.suit, anchor="nw", fill=color,
                         font=("TkDefaultFont", 17))
        self.create_text(64, 92, text=card.suit, fill=color,
                         font=("TkDefaultFont", 42))
        self.create_text(108, 157, text=card.rank, anchor="se", fill=color,
                         font=("TkDefaultFont", 18, "bold"))


class StrategyApp:
    def __init__(self, root: tk.Tk, controller: StrategyController | None = None) -> None:
        self.root = root
        self.controller = controller if controller is not None else StrategyController()
        self._closing_dialog = False
        root.title("Blackjack Trainer — Basic Strategy")
        root.minsize(820, 680)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()
        root.bind("<KeyPress>", self.on_key)
        self.refresh()

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Trainer.TButton", font=("TkDefaultFont", 11), padding=(14, 10))
        style.configure("Next.Trainer.TButton", font=("TkDefaultFont", 11, "bold"))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        main.grid(sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        tk.Label(main, text="BLACKJACK TRAINER", bg=BG, fg=ACCENT,
                 font=("TkDefaultFont", 22, "bold")).grid(row=0, sticky="w")
        tk.Label(main, text="Basic strategy · 6 decks · H17 · Double after split · No surrender",
                 bg=BG, fg=MUTED, font=("TkDefaultFont", 10)).grid(row=1, sticky="w", pady=(4, 12))
        self.progress_var = tk.StringVar(master=self.root)
        tk.Label(main, textvariable=self.progress_var, bg=BG, fg=MUTED).grid(row=2, sticky="w", pady=(0, 10))

        table = tk.Frame(main, bg=TABLE, padx=20, pady=15)
        table.grid(row=3, sticky="nsew")
        table.columnconfigure((0, 1), weight=1, uniform="hands")
        tk.Label(table, text="YOUR HAND", bg=TABLE, fg=TEXT,
                 font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, pady=(0, 8))
        tk.Label(table, text="DEALER UPCARD", bg=TABLE, fg=TEXT,
                 font=("TkDefaultFont", 11, "bold")).grid(row=0, column=1, pady=(0, 8))
        player_row = tk.Frame(table, bg=TABLE)
        player_row.grid(row=1, column=0)
        self.player_cards = [CardCanvas(player_row), CardCanvas(player_row)]
        for column, canvas in enumerate(self.player_cards):
            canvas.grid(row=0, column=column, padx=4)
        self.dealer_card = CardCanvas(table)
        self.dealer_card.grid(row=1, column=1)
        self.hand_var = tk.StringVar(master=self.root)
        tk.Label(table, textvariable=self.hand_var, bg=TABLE, fg=TEXT,
                 font=("TkDefaultFont", 12, "bold")).grid(row=2, column=0, pady=(10, 0))
        tk.Label(table, text="Choose the first action only", bg=TABLE, fg=MUTED).grid(row=2, column=1, pady=(10, 0))

        feedback_panel = tk.Frame(main, bg=PANEL, padx=16, pady=12)
        feedback_panel.grid(row=4, sticky="ew", pady=(12, 0))
        feedback_panel.columnconfigure(0, weight=1)
        self.feedback_var = tk.StringVar(master=self.root)
        self.feedback_label = tk.Label(feedback_panel, textvariable=self.feedback_var,
                                       bg=PANEL, fg=TEXT, anchor="w", justify="left",
                                       font=("TkDefaultFont", 12, "bold"), wraplength=720)
        self.feedback_label.grid(row=0, sticky="ew")
        self.stats_var = tk.StringVar(master=self.root)
        tk.Label(feedback_panel, textvariable=self.stats_var, bg=PANEL, fg=MUTED,
                 anchor="w").grid(row=1, sticky="w", pady=(8, 0))

        actions = tk.Frame(main, bg=BG)
        actions.grid(row=5, sticky="ew", pady=(14, 0))
        actions.columnconfigure((0, 1, 2, 3), weight=1, uniform="actions")
        self.action_buttons = {}
        for column, action in enumerate(Action):
            button = ttk.Button(actions, text=f"{action.label}  [{action.value}]",
                                style="Trainer.TButton", command=lambda value=action: self.on_answer(value))
            button.grid(row=0, column=column, sticky="ew", padx=(0, 8 if column < 3 else 0))
            button.bind("<KeyPress>", self.on_key)
            self.action_buttons[action] = button

        footer = tk.Frame(main, bg=BG)
        footer.grid(row=6, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        self.next_button = ttk.Button(footer, text="Next hand  [Enter]",
                                      style="Next.Trainer.TButton", command=self.on_next)
        self.next_button.grid(row=0, column=0, sticky="w")
        self.next_button.bind("<KeyPress>", self.on_key)
        self.quit_button = ttk.Button(footer, text="Quit  [Q / Esc]", style="Trainer.TButton",
                                      command=self.on_close)
        self.quit_button.grid(row=0, column=1, sticky="e")
        self.quit_button.bind("<KeyPress>", self.on_key)
        tk.Label(main, text="H / S / D / P: answer   ·   Enter / Space: next hand   ·   Q / Esc: quit",
                 bg=BG, fg=MUTED, font=("TkDefaultFont", 9)).grid(row=7, sticky="w", pady=(12, 0))

    def refresh(self) -> None:
        session = self.controller.session
        question = session.question
        if question is None:
            return
        for canvas, card in zip(self.player_cards, question.player_hand):
            canvas.show(card)
        self.dealer_card.show(question.dealer_upcard)
        hand = evaluate_hand(question.player_hand)
        if hand.is_blackjack:
            label = "Blackjack · 21"
        elif hand.pair_rank is not None:
            label = f"Pair of {hand.pair_rank} · Total {hand.total}"
        else:
            label = f"{'Soft' if hand.is_soft else 'Hard'} {hand.total}"
        self.hand_var.set(label)
        self.progress_var.set(f"Shoe {session.shoe_number}  ·  Cards remaining: {session.shoe.remaining}")
        self.stats_var.set(f"Answered: {session.answered}   Correct: {session.correct}   "
                           f"Incorrect: {session.incorrect}   Accuracy: {session.accuracy:.1f}%")
        feedback = session.feedback
        if feedback is None:
            self.feedback_var.set("What is the best opening action?")
            self.feedback_label.configure(fg=TEXT)
        else:
            verdict = "Correct!" if feedback.correct else f"Incorrect — you chose {feedback.chosen.label}."
            message = f"{verdict} Recommended: {feedback.recommended.label} ({feedback.recommended.value})."
            if self.controller.completed:
                message += " Session complete."
            self.feedback_var.set(message)
            self.feedback_label.configure(fg="#b4edc5" if feedback.correct else "#ffbaa9")
        for button in self.action_buttons.values():
            button.state(["!disabled" if self.controller.can_answer else "disabled"])
        self.next_button.state(["!disabled" if self.controller.can_advance else "disabled"])

    def on_answer(self, action: Action) -> None:
        if not self._closing_dialog and self.controller.submit(action) is not None:
            self.refresh()

    def on_next(self) -> None:
        if not self._closing_dialog and self.controller.next_question():
            self.refresh()

    def on_key(self, event) -> str | None:
        key = event.keysym.lower()
        if key in ("h", "s", "d", "p"):
            self.on_answer(Action(key.upper()))
        elif key in ("return", "kp_enter", "space"):
            self.on_next()
        elif key in ("q", "escape"):
            self.on_close()
        else:
            return None
        return "break"

    def on_close(self) -> None:
        if self._closing_dialog:
            return
        self._closing_dialog = True
        try:
            session = self.controller.session
            summary = (f"Answered: {session.answered}\nCorrect: {session.correct}\n"
                       f"Incorrect: {session.incorrect}\nAccuracy: {session.accuracy:.1f}%\n\n"
                       "Close the trainer?")
            accepted = self.controller.request_close(
                lambda: messagebox.askokcancel("End session", summary, parent=self.root))
            if accepted:
                self.root.destroy()
        finally:
            self._closing_dialog = False


def launch_gui(*, seed: int | None = None, round_limit: int | None = None) -> None:
    controller = StrategyController(StrategySession(seed=seed), round_limit=round_limit)
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError("Cannot open the GUI. Use a graphical desktop with working Tcl/Tk.") from error
    try:
        StrategyApp(root, controller)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
