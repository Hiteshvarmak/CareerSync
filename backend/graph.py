"""LangGraph orchestrator skeleton.

Routes an incoming user message to one of the four CareerPilot agents.
Each agent is currently a stub node; later phases replace the stub
bodies with real implementations (Planner in Phase 1, Tracker in
Phase 2, etc.) without touching the routing logic below.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from backend.models import AgentName, CareerPilotState

ROUTER_SYSTEM_PROMPT = """You route a user message to exactly one CareerPilot agent.
Reply with a single word, no punctuation, one of:
- planner: syllabus/deadline/task-list/schedule requests
- tracker: job application status, follow-ups, "did I hear back"
- skill_gap: resume vs job posting, skill gaps, courses to learn
- interview: mock interview practice, interview feedback
- unknown: anything else
"""

_AGENT_NAMES: set[AgentName] = {"planner", "tracker", "skill_gap", "interview"}


def _get_router_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def route(state: CareerPilotState) -> CareerPilotState:
    last_user_message = state["messages"][-1].content
    llm = _get_router_llm()
    reply = llm.invoke(
        [
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", last_user_message),
        ]
    )
    choice = reply.content.strip().lower()
    active_agent: AgentName = choice if choice in _AGENT_NAMES else "unknown"
    return {"active_agent": active_agent}


def _stub_agent(name: str):
    def node(state: CareerPilotState) -> CareerPilotState:
        last_user_message = state["messages"][-1].content
        reply = AIMessage(
            content=(
                f"[{name} agent stub] Not implemented yet. "
                f"You said: {last_user_message!r}"
            )
        )
        return {"messages": [reply]}

    return node


def _fallback(state: CareerPilotState) -> CareerPilotState:
    reply = AIMessage(
        content="I couldn't tell which agent should handle that. "
        "Try asking about your tasks, applications, skill gaps, or interview prep."
    )
    return {"messages": [reply]}


def _select_agent(state: CareerPilotState) -> str:
    return state["active_agent"]


def build_graph():
    graph = StateGraph(CareerPilotState)

    graph.add_node("route", route)
    graph.add_node("planner", _stub_agent("planner"))
    graph.add_node("tracker", _stub_agent("tracker"))
    graph.add_node("skill_gap", _stub_agent("skill_gap"))
    graph.add_node("interview", _stub_agent("interview"))
    graph.add_node("unknown", _fallback)

    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        _select_agent,
        {
            "planner": "planner",
            "tracker": "tracker",
            "skill_gap": "skill_gap",
            "interview": "interview",
            "unknown": "unknown",
        },
    )
    for node in ("planner", "tracker", "skill_gap", "interview", "unknown"):
        graph.add_edge(node, END)

    return graph.compile()
