from __future__ import annotations

from backend.pipeline.zone2.agents.alignment_agent import run_alignment_agent
from backend.pipeline.zone2.agents.crop_planner_agent import run_crop_planner_agent
from backend.pipeline.zone2.agents.scoring_agent import run_scoring_agent
from backend.pipeline.zone2.state import VideoJobState


def build_zone2_graph():
    try:
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(VideoJobState)
        graph.add_node("scoring_agent", run_scoring_agent)
        graph.add_node("crop_planner_agent", run_crop_planner_agent)
        graph.add_node("alignment_agent", run_alignment_agent)
        graph.add_edge(START, "scoring_agent")
        graph.add_edge("scoring_agent", "crop_planner_agent")
        graph.add_edge("crop_planner_agent", "alignment_agent")
        graph.add_edge("alignment_agent", END)
        return graph.compile()
    except Exception:
        return None


def run_zone2_graph(state: VideoJobState) -> VideoJobState:
    graph = build_zone2_graph()
    if graph is None:
        state = run_scoring_agent(state)
        state = run_crop_planner_agent(state)
        state = run_alignment_agent(state)
        return state
    return graph.invoke(state)
