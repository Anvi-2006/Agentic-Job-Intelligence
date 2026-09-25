from langgraph.graph import END, START, StateGraph

from backend.app.agents.nodes import (
    initialize_agent,
    understand_search_intent,
    search_jobs_node,
)
from backend.app.agents.state import AgentState


def build_search_graph():
    graph = StateGraph(AgentState)

    graph.add_node("initialize", initialize_agent)
    graph.add_node("understand_intent", understand_search_intent)
    graph.add_node("search_jobs", search_jobs_node)

    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "understand_intent")
    graph.add_edge("understand_intent", "search_jobs")
    graph.add_edge("search_jobs", END)

    return graph.compile()


search_graph = build_search_graph()
