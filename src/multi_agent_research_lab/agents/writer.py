"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesizes research notes, analysis notes, and source list into a final report.
        """
        llm_client = LLMClient()

        # Build sources string for context
        sources_list = "\n".join(
            f"- [{doc.title}]({doc.url or 'No URL'}): {doc.snippet}"
            for doc in state.sources
        )

        system_prompt = (
            "You are a senior science editor. Write a structured research briefing based on the provided notes. "
            "You must cite the provided sources where applicable using inline markdown links e.g. [Title](URL).\n\n"
            "Your output must follow this exact markdown header structure:\n"
            "## Core Question\n"
            "## Main Positions\n"
            "## Evidence For\n"
            "## Evidence Against\n"
            "## Methodological Concerns\n"
            "## Proposed Experiments\n"
            "## Final Judgment\n\n"
            "Ensure the final judgment notes key uncertainties and open research gaps. Output ONLY the briefing."
        )

        user_prompt = (
            f"User Research Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Analysis Notes:\n{state.analysis_notes}\n\n"
            f"Sources:\n{sources_list}"
        )

        response = llm_client.complete(system_prompt, user_prompt)

        state.final_answer = response.content

        state.add_trace_event("writer_execution", {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        })

        state.agent_results.append(AgentResult(
            agent=AgentName.WRITER,
            content="Completed final research briefing draft.",
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd
            }
        ))

        return state
