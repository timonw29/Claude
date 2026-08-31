import argparse

from . import memory
from .agent import Agent


def main():
    parser = argparse.ArgumentParser(
        prog="moni", description="Moni - dein persönlicher Claude-Assistent"
    )
    parser.add_argument(
        "--voice", action="store_true", help="Sprachmodus (Mikrofon + Sprachausgabe)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Tool-Aufrufe (Shell/Dateien) ohne Rückfrage erlauben",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Gespeicherten Gesprächsverlauf löschen"
    )
    args = parser.parse_args()

    if args.reset:
        memory.clear_history()
        print("Verlauf gelöscht.")
        return

    messages = memory.load_history()
    agent = Agent(auto_confirm=args.yes)

    voice = None
    if args.voice:
        from . import voice as voice_module

        voice = voice_module

    print("Moni ist bereit. 'exit' zum Beenden, 'reset' um den Verlauf zu löschen.\n")

    while True:
        if voice:
            user_input = voice.listen()
            if user_input is None:
                continue
            print(f"Du: {user_input}")
        else:
            try:
                user_input = input("Du: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue

        if user_input.lower() in ("exit", "quit"):
            break
        if user_input.lower() == "reset":
            messages = []
            memory.clear_history()
            print("Verlauf gelöscht.")
            continue

        messages.append({"role": "user", "content": user_input})
        messages, reply_text = agent.run_turn(messages)
        print(f"Moni: {reply_text}\n")

        if voice:
            voice.speak(reply_text)

        memory.save_history(messages)


if __name__ == "__main__":
    main()
