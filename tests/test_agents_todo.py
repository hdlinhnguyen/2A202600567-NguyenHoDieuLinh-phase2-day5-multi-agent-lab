from unittest.mock import MagicMock, patch
import pytest

from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMResponse


@patch("multi_agent_research_lab.services.llm_client.LLMClient.complete")
def test_supervisor_routes_to_researcher(mock_complete: MagicMock) -> None:
    # Mock Supervisor JSON decision
    mock_complete.return_value = LLMResponse(
        content='{"next_agent": "researcher", "reason": "Research notes are missing."}',
        input_tokens=10,
        output_tokens=15,
        cost_usd=0.00001
    )
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    updated_state = SupervisorAgent().run(state)
    assert updated_state.route_history == ["researcher"]
    assert len(updated_state.agent_results) == 1
    assert "researcher" in updated_state.agent_results[0].content


@patch("multi_agent_research_lab.services.llm_client.LLMClient.complete")
def test_researcher_compiles_notes(mock_complete: MagicMock) -> None:
    # First call generates query list, second compiles notes
    mock_complete.side_effect = [
        LLMResponse(content='["explain multi-agent workflows"]', input_tokens=5, output_tokens=5, cost_usd=0.00001),
        LLMResponse(content='Compiled research findings.', input_tokens=10, output_tokens=10, cost_usd=0.00001)
    ]
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    updated_state = ResearcherAgent().run(state)
    assert updated_state.research_notes == "Compiled research findings."
    assert len(updated_state.sources) > 0
