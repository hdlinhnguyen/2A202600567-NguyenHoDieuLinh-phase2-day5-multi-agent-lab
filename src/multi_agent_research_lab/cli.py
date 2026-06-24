"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


import json
import os
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report, render_html_report


def run_baseline_workflow(query: str) -> ResearchState:
    """Execute a single-agent baseline LLM call."""
    llm_client = LLMClient()
    state = ResearchState(request=ResearchQuery(query=query))
    
    system_prompt = (
        "You are an expert research assistant. Write a detailed, structured research briefing "
        "answering the user query. Break your answer into clear markdown sections."
    )
    response = llm_client.complete(system_prompt, query)
    
    state.final_answer = response.content
    state.agent_results.append(AgentResult(
        agent=AgentName.WRITER,
        content=response.content,
        metadata={
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd
        }
    ))
    return state


def run_multi_agent_workflow(query: str) -> ResearchState:
    """Execute the multi-agent workflow."""
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a real single-agent baseline LLM call."""
    _init()
    console.print(f"[bold green]Running Baseline on query: {query}[/bold green]")
    state = run_baseline_workflow(query)
    console.print(Panel.fit(state.final_answer or "No response generated.", title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""
    _init()
    console.print(f"[bold green]Running Multi-Agent Workflow on query: {query}[/bold green]")
    try:
        state = run_multi_agent_workflow(query)
        console.print(Panel.fit(state.final_answer or "No response generated.", title="Multi-Agent Final Answer"))
        
        # Output minimal results logs
        console.print(f"[bold blue]Completed in {state.iteration} iterations.[/bold blue]")
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both baseline and multi-agent systems and compile comparison reports."""
    _init()
    os.makedirs("reports", exist_ok=True)

    console.print("[bold green]>>> Running Single-Agent Baseline...[/bold green]")
    baseline_state, baseline_metrics = run_benchmark("Single-Agent Baseline", query, run_baseline_workflow)
    
    console.print("[bold green]>>> Running Multi-Agent Workflow...[/bold green]")
    try:
        multi_state, multi_metrics = run_benchmark("Multi-Agent Workflow", query, run_multi_agent_workflow)
    except Exception as e:
        console.print(f"[bold red]Multi-Agent Workflow failed: {e}[/bold red]")
        raise typer.Exit(code=3) from e

    # Write multi-agent trace file
    trace_path = "reports/trace_multi_agent.json"
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump({
            "query": query,
            "multi_agent_trace": multi_state.trace,
            "multi_agent_results": [res.model_dump() for res in multi_state.agent_results]
        }, f, indent=2)
    console.print(f"[bold blue]Execution trace file written to: {trace_path}[/bold blue]")

    # Render benchmark report
    report_content = render_markdown_report(
        [baseline_metrics, multi_metrics],
        baseline_output=baseline_state.final_answer or "",
        multi_output=multi_state.final_answer or ""
    )
    report_path = "reports/benchmark_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    console.print(f"[bold blue]Benchmark comparison report written to: {report_path}[/bold blue]")

    # Render HTML report
    html_content = render_html_report(
        [baseline_metrics, multi_metrics],
        baseline_output=baseline_state.final_answer or "",
        multi_output=multi_state.final_answer or ""
    )
    html_path = "reports/benchmark_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    console.print(f"[bold blue]Benchmark comparison HTML report written to: {html_path}[/bold blue]")

    console.print(Panel.fit(report_content, title="Benchmark Results Report"))


if __name__ == "__main__":
    app()
