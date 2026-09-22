from langgraph.graph import END, START, StateGraph

from backend.app.agents.nodes import (
    initialize_agent,
    understand_search_intent,
    search_jobs_node,
    understand_jobs_node,
    match_and_score_jobs_node,
    rank_jobs_node,
    decide_applications_node,
    prepare_application_packages_node,
)
from backend.app.agents.state import AgentState


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("initialize", initialize_agent)
    graph.add_node("understand_intent", understand_search_intent)
    graph.add_node("search_jobs", search_jobs_node)
    graph.add_node("understand_jobs", understand_jobs_node)
    graph.add_node("match_and_score_jobs", match_and_score_jobs_node)
    graph.add_node("rank_jobs", rank_jobs_node)
    graph.add_node("decide_applications", decide_applications_node)
    graph.add_node(
        "prepare_application_packages",
        prepare_application_packages_node,
    )
    
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "understand_intent")
    graph.add_edge("understand_intent", "search_jobs")
    graph.add_edge("search_jobs", "understand_jobs")
    graph.add_edge("understand_jobs", "match_and_score_jobs")
    graph.add_edge("match_and_score_jobs", "rank_jobs")
    graph.add_edge("rank_jobs", "decide_applications")
    graph.add_edge(
        "decide_applications",
        "prepare_application_packages",
    )
    graph.add_edge(
        "prepare_application_packages",
        END,
    )
    return graph.compile()


def build_search_graph():
    graph = StateGraph(AgentState)

    graph.add_node("initialize", initialize_agent)
    graph.add_node("understand_intent", understand_search_intent)
    graph.add_node("search_jobs", search_jobs_node)
    graph.add_node("understand_jobs", understand_jobs_node)
    graph.add_node("rank_jobs", rank_jobs_node)

    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "understand_intent")
    graph.add_edge("understand_intent", "search_jobs")
    graph.add_edge("search_jobs", "understand_jobs")
    graph.add_edge("understand_jobs", "rank_jobs")
    graph.add_edge("rank_jobs", END)

    return graph.compile()


search_graph = build_search_graph()