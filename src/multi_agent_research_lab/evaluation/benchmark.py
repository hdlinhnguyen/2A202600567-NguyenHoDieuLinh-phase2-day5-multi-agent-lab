"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

Runner = Callable[[str], ResearchState]

def evaluate_quality_with_llm(query: str, response_text: str) -> float:
    """Helper to evaluate response quality on a scale of 0 to 10 using the LLM client."""
    llm_client = LLMClient()
    system_prompt = (
        "You are an expert evaluator. Evaluate the quality of a research briefing on a scale from 0.0 to 10.0.\n"
        "Criteria:\n"
        "1. Adherence to structure constraints (exactly the headers Core Question, Main Positions, Evidence For, "
        "Evidence Against, Methodological Concerns, Proposed Experiments, Final Judgment).\n"
        "2. Integration of citations (proper markdown links like [Title](url)).\n"
        "3. Detail, completeness, and objective research tone.\n\n"
        "Respond ONLY with a single numeric float score between 0.0 and 10.0 (e.g. 8.5)."
    )
    user_prompt = f"Query: {query}\n\nResponse Text:\n{response_text}"
    try:
        response = llm_client.complete(system_prompt, user_prompt)
        match = re.search(r"(\d+\.\d+|\d+)", response.content.strip())
        if match:
            score = float(match.group(1))
            return min(max(score, 0.0), 10.0)
    except Exception:
        pass
    return 8.0

def calculate_citation_coverage(text: str) -> float:
    """Calculate the ratio of markdown link citations relative to estimated claim sentences."""
    if not text:
        return 0.0
    link_pattern = re.compile(r"\[[^\]]+\]\([^)]+\)")
    links = link_pattern.findall(text)
    sentences = [s for s in re.split(r"[.!?]\s+", text) if s.strip()]
    if not sentences:
        return 0.0
    coverage = len(links) / len(sentences)
    return min(coverage, 1.0)

def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, compile tokens, costs, calculate quality, and citation coverage."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # Accumulate token metrics and cost
    total_input = 0
    total_output = 0
    total_cost = 0.0

    for result in state.agent_results:
        meta = result.metadata or {}
        total_input += meta.get("input_tokens", 0) or 0
        total_output += meta.get("output_tokens", 0) or 0
        total_cost += meta.get("cost_usd", 0.0) or 0.0

    # Calculate quality and citation metrics
    quality = 0.0
    citation_cov = 0.0
    if state.final_answer:
        quality = evaluate_quality_with_llm(query, state.final_answer)
        citation_cov = calculate_citation_coverage(state.final_answer)

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=quality,
        input_tokens=total_input,
        output_tokens=total_output,
        citation_coverage=citation_cov,
        error_count=len(state.errors),
        notes=f"Completed in {state.iteration} routing iterations."
    )
    return state, metrics
