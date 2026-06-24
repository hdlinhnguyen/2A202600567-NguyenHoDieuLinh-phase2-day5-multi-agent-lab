"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Uses LLM router decision, with programmatic guards for max iterations.
        """
        settings = get_settings()

        # Guardrail: Limit maximum iterations
        if state.iteration >= settings.max_iterations:
            next_agent = "done"
            state.record_route(next_agent)
            state.add_trace_event("supervisor_decision", {"next_agent": next_agent, "reason": "Max iterations reached"})
            return state

        # If we are close to the limit, force final steps
        if state.iteration >= settings.max_iterations - 2:
            if not state.final_answer:
                next_agent = "writer"
            else:
                next_agent = "done"
            state.record_route(next_agent)
            state.add_trace_event("supervisor_decision", {"next_agent": next_agent, "reason": "Approaching max iterations"})
            return state

        system_prompt = (
            "You are the Supervisor of a multi-agent research lab workflow.\n"
            "Your role is to orchestrate worker agents to deliver a perfect research briefing.\n"
            "Workers available:\n"
            "- researcher: gathers facts and sources, compiles research notes. Runs first or if more info is needed.\n"
            "- analyst: analyzes research notes, compares positions, identifies experimental gaps. Runs after researcher notes are populated.\n"
            "- writer: synthesizes research and analysis notes into a final briefing matching user query requirements.\n"
            "- critic: reviews the final briefing for accuracy, style, and instructions compliance. Runs after writer completes the draft.\n"
            "- done: select this only if the final answer is complete and has successfully passed review/critic checks.\n\n"
            "Respond ONLY with a JSON object in this format:\n"
            "{\n"
            "  \"next_agent\": \"researcher\" | \"analyst\" | \"writer\" | \"critic\" | \"done\",\n"
            "  \"reason\": \"Explanation of decision based on what notes are present and current state\"\n"
            "}"
        )

        user_prompt = (
            f"User Query: {state.request.query}\n"
            f"Route History: {state.route_history}\n"
            f"Current Iteration: {state.iteration}\n"
            f"Has Research Notes: {state.research_notes is not None}\n"
            f"Has Analysis Notes: {state.analysis_notes is not None}\n"
            f"Has Final Answer: {state.final_answer is not None}\n"
            f"Errors/Critic Feedback: {state.errors}\n"
        )

        llm_client = LLMClient()
        response = llm_client.complete(system_prompt, user_prompt)

        # Parse decision
        try:
            content_str = response.content.strip()
            if content_str.startswith("```"):
                content_str = content_str.split("```")[1]
                if content_str.startswith("json"):
                    content_str = content_str[4:]
            decision = json.loads(content_str.strip())
            next_agent = decision.get("next_agent", "").strip().lower()
            reason = decision.get("reason", "Standard flow")
        except Exception:
            reason = "Failed to parse JSON decision, fell back to programmatic rules."
            if not state.research_notes:
                next_agent = "researcher"
            elif not state.analysis_notes:
                next_agent = "analyst"
            elif not state.final_answer:
                next_agent = "writer"
            else:
                next_agent = "done"

        # Validate agent selection
        valid_agents = ["researcher", "analyst", "writer", "critic", "done"]
        if next_agent not in valid_agents:
            next_agent = "done"

        state.record_route(next_agent)
        state.add_trace_event("supervisor_decision", {
            "next_agent": next_agent,
            "reason": reason,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        })

        state.agent_results.append(AgentResult(
            agent=AgentName.SUPERVISOR,
            content=f"Decided route: {next_agent}. Reason: {reason}",
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd
            }
        ))

        return state
