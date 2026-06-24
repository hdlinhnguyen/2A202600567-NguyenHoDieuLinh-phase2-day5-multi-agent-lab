"""LangGraph workflow skeleton."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


from langgraph.graph import StateGraph, END
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

def run_supervisor(state: ResearchState) -> ResearchState:
    return SupervisorAgent().run(state)

def run_researcher(state: ResearchState) -> ResearchState:
    return ResearcherAgent().run(state)

def run_analyst(state: ResearchState) -> ResearchState:
    return AnalystAgent().run(state)

def run_writer(state: ResearchState) -> ResearchState:
    return WriterAgent().run(state)

def run_critic(state: ResearchState) -> ResearchState:
    return CriticAgent().run(state)

def route_next(state: ResearchState) -> str:
    if not state.route_history:
        return "done"
    next_step = state.route_history[-1]
    if next_step in ["researcher", "analyst", "writer", "critic", "done"]:
        return next_step
    return "done"

class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> StateGraph:
        """Create a LangGraph graph."""
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("supervisor", run_supervisor)
        workflow.add_node("researcher", run_researcher)
        workflow.add_node("analyst", run_analyst)
        workflow.add_node("writer", run_writer)
        workflow.add_node("critic", run_critic)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add transitions
        workflow.add_conditional_edges(
            "supervisor",
            route_next,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "done": END
            }
        )

        # Workers return control to supervisor
        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("analyst", "supervisor")
        workflow.add_edge("writer", "supervisor")
        workflow.add_edge("critic", "supervisor")

        return workflow

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        workflow_graph = self.build().compile()
        
        with trace_span("multi_agent_workflow") as span:
            result = workflow_graph.invoke(state)
            
        if isinstance(result, ResearchState):
            return result
        elif isinstance(result, dict):
            # Fallback if LangGraph returns raw dict
            return ResearchState(**result)
            
        return state
