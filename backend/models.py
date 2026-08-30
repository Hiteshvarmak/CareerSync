from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages


AgentName = Literal["planner", "tracker", "skill_gap", "interview", "unknown"]


class CareerPilotState(TypedDict):
    """Shared state threaded through the LangGraph orchestrator."""

    messages: Annotated[list, add_messages]
    active_agent: AgentName
