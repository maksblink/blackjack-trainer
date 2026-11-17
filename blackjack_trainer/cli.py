"""Interactive terminal practice for the first blackjack decision only."""

from collections.abc import Callable

from blackjack_trainer.hands import evaluate_hand
from blackjack_trainer.training import Question, StrategySession


def describe_question(question: Question) -> str:
    hand = evaluate_hand(question.player_hand)
    if hand.is_blackjack:
        label = "Blackjack (21)"
    elif hand.pair_rank is not None:
        label = f"Pair of {hand.pair_rank} | total {hand.total}"
    else:
        label = f"{'Soft' if hand.is_soft else 'Hard'} {hand.total}"
    cards = " ".join(str(card) for card in question.player_hand)
    return f"Your cards: {cards} | {label}\nDealer upcard: {question.dealer_upcard}"


def run_cli(
    session: StrategySession | None = None,
    *,
    round_limit: int | None = None,
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] | None = None,
) -> StrategySession:
    """Run until quit, EOF, Ctrl+C, or the requested number of new answers."""
    if round_limit is not None and (isinstance(round_limit, bool)
                                    or not isinstance(round_limit, int) or round_limit < 1):
        raise ValueError("round_limit must be a positive integer")
    session = session if session is not None else StrategySession()
    read = input_func if input_func is not None else input
    write = output_func if output_func is not None else print
    initial_answers = session.answered
    write("BLACKJACK BASIC STRATEGY TRAINER")
    write("Six-deck H17 / DAS / no surrender. Practice the opening decision only.")
    write("H = Hit | S = Stand | D = Double | P = Split | Q = Quit")
    try:
        while round_limit is None or session.answered - initial_answers < round_limit:
            shoe_number = session.shoe_number
            if session.question is None or session.feedback is not None:
                session.next_question()
            if session.shoe_number != shoe_number:
                write("New shoe: all cards have been reshuffled.")
            write(f"\nQuestion {session.answered + 1}")
            write(describe_question(session.question))
            while True:
                answer = read("Your action [H/S/D/P/Q]: ").strip().upper()
                if answer == "Q":
                    return session
                try:
                    feedback = session.submit(answer)
                except ValueError:
                    write("Invalid action. Enter H, S, D, P, or Q.")
                    continue
                break
            verdict = "Correct!" if feedback.correct else "Incorrect."
            write(f"{verdict} Recommended: {feedback.recommended.value} ({feedback.recommended.label}).")
            write(f"Accuracy: {session.correct}/{session.answered} ({session.accuracy:.1f}%)")
            if round_limit is not None and session.answered - initial_answers >= round_limit:
                break
            while True:
                command = read("Enter = next question | Q = quit: ").strip().upper()
                if command == "Q":
                    return session
                if not command:
                    break
                write("Press Enter to continue, or Q to quit.")
    except (EOFError, KeyboardInterrupt):
        write("\nSession ended.")
    finally:
        write("\nSESSION SUMMARY")
        write(f"Answered: {session.answered} | Correct: {session.correct} | Incorrect: {session.incorrect}")
        write(f"Accuracy: {session.accuracy:.1f}%")
    return session
