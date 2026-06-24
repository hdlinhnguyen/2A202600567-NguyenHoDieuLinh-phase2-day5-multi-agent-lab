"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Generates queries, queries search client, filters duplicates, and compiles notes.
        """
        llm_client = LLMClient()
        search_client = SearchClient()

        # Step 1: Generate search queries
        query_gen_system = (
            "You are a search query optimizer. Generate up to 3 distinct search queries to gather comprehensive "
            "academic, industry, and benchmark information to answer the user's research query.\n"
            "Respond ONLY with a JSON array of strings.\n"
            "Example format: [\"query 1\", \"query 2\"]"
        )
        query_gen_user = f"Research Query: {state.request.query}"

        response_queries = llm_client.complete(query_gen_system, query_gen_user)

        total_input_tokens = response_queries.input_tokens or 0
        total_output_tokens = response_queries.output_tokens or 0
        total_cost = response_queries.cost_usd or 0.0

        try:
            content_str = response_queries.content.strip()
            if content_str.startswith("```"):
                content_str = content_str.split("```")[1]
                if content_str.startswith("json"):
                    content_str = content_str[4:]
            search_queries = json.loads(content_str.strip())
            if not isinstance(search_queries, list):
                search_queries = [state.request.query]
        except Exception:
            search_queries = [state.request.query]

        # Step 2: Execute search queries and collect documents
        collected_docs = []
        seen_urls = set()
        for q in search_queries:
            results = search_client.search(q, max_results=state.request.max_sources)
            for doc in results:
                url_key = doc.url or doc.title
                if url_key not in seen_urls:
                    seen_urls.add(url_key)
                    collected_docs.append(doc)

        state.sources.extend(collected_docs)

        # Step 3: Synthesize research notes
        sources_str = "\n\n".join(
            f"Source: {doc.title} ({doc.url or 'No URL'})\nContent: {doc.snippet}"
            for doc in collected_docs
        )

        synthesis_system = (
            "You are an expert researcher. Synthesize the provided raw sources into concise, structured "
            "research notes addressing the user's query. Group findings by theme, cite sources clearly by title/URL, "
            "and capture concrete statistics, empirical findings, and viewpoints. Focus on factual accuracy."
        )
        synthesis_user = (
            f"Research Question: {state.request.query}\n\n"
            f"Sources Found:\n{sources_str}"
        )

        response_synthesis = llm_client.complete(synthesis_system, synthesis_user)

        total_input_tokens += response_synthesis.input_tokens or 0
        total_output_tokens += response_synthesis.output_tokens or 0
        total_cost += response_synthesis.cost_usd or 0.0

        state.research_notes = response_synthesis.content

        # Record events
        state.add_trace_event("researcher_execution", {
            "queries": search_queries,
            "sources_collected_count": len(collected_docs),
            "input_tokens": response_synthesis.input_tokens,
            "output_tokens": response_synthesis.output_tokens,
            "cost_usd": response_synthesis.cost_usd
        })

        state.agent_results.append(AgentResult(
            agent=AgentName.RESEARCHER,
            content=f"Compiled notes from {len(collected_docs)} sources.",
            metadata={
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cost_usd": total_cost,
                "queries": search_queries
            }
        ))

        return state
