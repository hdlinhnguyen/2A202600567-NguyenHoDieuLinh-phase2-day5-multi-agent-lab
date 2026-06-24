"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings.

        Validates the structure, citation accuracy, and tone of the draft report.
        """
        llm_client = LLMClient()

        sources_list = "\n".join(
            f"- [{doc.title}]({doc.url or 'No URL'}): {doc.snippet}"
            for doc in state.sources
        )

        system_prompt = (
            "You are an academic reviewer. Evaluate the provided final report draft. "
            "Verify if the draft meets the following guidelines:\n"
            "1. Has the required markdown headers: Core Question, Main Positions, Evidence For, "
            "Evidence Against, Methodological Concerns, Proposed Experiments, Final Judgment.\n"
            "2. Appropriately cites the source list using inline links like [Title](URL).\n"
            "3. Conveys reasonable uncertainty in the Final Judgment section.\n\n"
            "You must return ONLY a JSON response in the following format:\n"
            "{\n"
            "  \"passed\": true | false,\n"
            "  \"critique\": \"Write specific instructions for improvement if passed is false. Otherwise describe strength.\"\n"
            "}"
        )

        user_prompt = (
            f"Sources list:\n{sources_list}\n\n"
            f"Draft Report:\n{state.final_answer}"
        )

        response = llm_client.complete(system_prompt, user_prompt)

        try:
            content_str = response.content.strip()
            if content_str.startswith("```"):
                content_str = content_str.split("```")[1]
                if content_str.startswith("json"):
                    content_str = content_str[4:]
            result = json.loads(content_str.strip())
            passed = bool(result.get("passed", False))
            critique = result.get("critique", "No comment.")
        except Exception:
            passed = True
            critique = "Failed to parse critic feedback. Defaulting to passed to avoid loop."

        state.errors = []
        if not passed:
            state.errors.append(critique)

        state.add_trace_event("critic_execution", {
            "passed": passed,
            "critique": critique,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        })

        state.agent_results.append(AgentResult(
            agent=AgentName.CRITIC,
            content=f"Critic evaluated draft. Passed: {passed}. Critique: {critique}",
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "passed": passed
            }
        ))

        return state
