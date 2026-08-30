from unittest.mock import patch

from langchain_core.messages import AIMessage

from backend.graph import build_graph


def test_route_to_planner_stub():
    app = build_graph()
    with patch("backend.graph._get_router_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = AIMessage(content="planner")
        result = app.invoke(
            {
                "messages": [("human", "what's on my plate today?")],
                "active_agent": "unknown",
            }
        )
    assert result["active_agent"] == "planner"
    assert "[planner agent stub]" in result["messages"][-1].content


def test_unrecognized_route_falls_back():
    app = build_graph()
    with patch("backend.graph._get_router_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = AIMessage(content="something else")
        result = app.invoke(
            {"messages": [("human", "hello")], "active_agent": "unknown"}
        )
    assert result["active_agent"] == "unknown"
    assert "couldn't tell" in result["messages"][-1].content
