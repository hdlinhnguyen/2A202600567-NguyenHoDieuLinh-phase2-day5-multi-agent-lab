"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Extracts key claims, performs critique of viewpoints, and identifies experiment proposals.
        """
        llm_client = LLMClient()

        system_prompt = (
            "You are an expert analyst. Read the provided research notes and perform a deep, critical analysis. "
            "Analyze the core research question by outlining:\n"
            "1. Major viewpoints / schools of thought.\n"
            "2. Evidence supporting the primary claim.\n"
            "3. Evidence challenging the claim.\n"
            "4. Methodological concerns (e.g. token budget unfairness, inference compute matching, prompt engineering differences).\n"
            "5. Three (3) concrete, rigorous experiments that could resolve the debate.\n\n"
            "Keep your output structured using markdown headers."
        )

        user_prompt = (
            f"Research Question: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}"
        )

        response = llm_client.complete(system_prompt, user_prompt)

        state.analysis_notes = response.content

        state.add_trace_event("analyst_execution", {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        })

        state.agent_results.append(AgentResult(
            agent=AgentName.ANALYST,
            content="Synthesized structured analysis insights.",
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd
            }
        ))

        return state
