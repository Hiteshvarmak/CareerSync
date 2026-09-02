"""CLI entrypoint for exercising the orchestrator during development."""

from dotenv import load_dotenv

from backend.db import init_db
from backend.graph import build_graph

load_dotenv()


def main() -> None:
    init_db()
    app = build_graph()
    print("CareerPilot orchestrator skeleton. Type 'quit' to exit.")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        result = app.invoke(
            {"messages": [("human", user_input)], "active_agent": "unknown"}
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
