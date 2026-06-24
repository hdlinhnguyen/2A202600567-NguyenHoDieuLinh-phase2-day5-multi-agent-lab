"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any


import logging

logger = logging.getLogger("multi_agent_research_lab.observability")

@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context used to trace execution steps."""
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    logger.info(f"[SPAN START] {name} - Attributes: {attributes or {}}")
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        logger.info(f"[SPAN END] {name} - Duration: {span['duration_seconds']:.4f}s")
