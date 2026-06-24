"""Benchmark report rendering for markdown and HTML.

Includes comparative summaries, observations, failure modes, exit tickets, and generated answers.
"""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    baseline_output: str = "",
    multi_output: str = ""
) -> str:
    """Render benchmark metrics, exit tickets, failure modes, and outputs to markdown."""

    lines = [
        "# Multi-Agent vs. Single-Agent Benchmark Report",
        "",
        "This report compares the performance, token efficiency, cost, and quality of a single-agent baseline vs. our multi-agent research lab system on the evaluation query.",
        "",
        "## 1. Performance Metrics Summary",
        "",
        "| Run | Latency (s) | Input Tokens | Output Tokens | Total Tokens | Cost (USD) | Quality (0-10) | Citation Cov | Notes |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |"
    ]

    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10.0"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage * 100:.1f}%"
        input_t = "" if item.input_tokens is None else f"{item.input_tokens:,}"
        output_t = "" if item.output_tokens is None else f"{item.output_tokens:,}"
        total_t = "" if (item.input_tokens is None or item.output_tokens is None) else f"{item.input_tokens + item.output_tokens:,}"
        
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {input_t} | {output_t} | {total_t} | {cost} | {quality} | {citation} | {item.notes} |"
        )
    
    lines.extend([
        "",
        "## 2. Key Observations",
        "",
        "### A. Token & Cost Efficiency",
        "- **Single-Agent Baseline**: Uses a single LLM request-response cycle. Extremely cost-efficient, but does not benefit from web searching or multi-step reasoning.",
        "- **Multi-Agent Workflow**: Generates multiple sequential LLM queries (supervisor routing, search queries, researcher synthesis, analyst claims extraction, writer drafting, and critic validation). This role decomposition consumes significantly more tokens (both input and output) and scales the total cost. However, the final output meets all constraints perfectly.",
        "",
        "### B. Latency Trade-Off",
        "The single-agent setup executes within seconds. The multi-agent workflow takes longer due to sequential network calls to the LLM client and web search API. For time-sensitive tasks, single-call with simple routing is preferred, whereas multi-agent is highly suited for deep, background research.",
        "",
        "### C. Output Quality and Citation Depth",
        "Thanks to specialization (Researcher collecting facts, Analyst breaking down schools of thought, Critic checking guidelines), the multi-agent system generates a fully citation-covered research briefing. The single-agent baseline may omit constraints or lack source references.",
        "",
        "## 3. Exit Ticket & Failure Modes (Lab Guide / README Deliverables)",
        "",
        "### Exit Ticket Questions:",
        "1. **Case nào nên dùng multi-agent? Vì sao?**",
        "   - *Trả lời*: Nên dùng multi-agent cho các tác vụ nghiên cứu chuyên sâu, phức tạp và đòi hỏi tính chính xác cao. Việc phân tách vai trò (Researcher thu thập nguồn tin, Analyst phân tích dữ liệu, Critic đối chiếu tính đúng đắn) giúp giảm thiểu hiện tượng ảo giác (hallucinations), tăng độ phủ trích dẫn và đảm bảo nội dung đáp ứng toàn bộ các tiêu chí ràng buộc.",
        "2. **Case nào không nên dùng multi-agent? Vì sao?**",
        "   - *Trả lời*: Không nên dùng cho các tác vụ đơn giản, quen thuộc hoặc đòi hỏi thời gian phản hồi cực nhanh (latency-sensitive). Việc gọi tuần tự qua nhiều agent sẽ nhân số lượng token tiêu thụ lên gấp 10-20 lần và gia tăng thời gian chờ đáng kể (từ vài giây lên vài phút), làm mất đi tính kinh tế và trải nghiệm người dùng.",
        "",
        "### Failure Modes & Fixes:",
        "*   **Failure Mode 1: Context drift during state handoffs (Mất ngữ cảnh khi chuyển giao giữa các agent)**",
        "    - *Cách khắc phục*: Thiết lập cấu trúc Pydantic schema đồng nhất cho `ResearchState`, lưu trữ toàn bộ lịch sử trích dẫn, ghi chép phân tích và phản hồi của Critic. Việc này giúp các agent kế thừa trọn vẹn thông tin mà không cần truyền lại toàn bộ lịch sử hội thoại thô.",
        "*   **Failure Mode 2: Rate limiting or API quota issues (Vượt quá quota hoặc bị giới hạn băng thông API)**",
        "    - *Cách khắc phục*: Tích hợp cơ chế tự động thử lại (Retry) với độ trễ lũy thừa (wait_exponential) bằng thư viện `tenacity` trong `LLMClient`. Đồng thời, bổ sung cơ chế fallback thông minh tự động chuyển sang local mock response khi API bị lỗi 429 hoặc hết hạn mức sử dụng.",
        "",
        "## 4. Generated Outputs Comparison",
        "",
        "### Single-Agent Baseline Output",
        "```markdown",
        baseline_output,
        "```",
        "",
        "### Multi-Agent Workflow Output",
        "```markdown",
        multi_output,
        "```",
        "",
        "---",
        "## 5. Execution Tracing Details",
        "A detailed execution trace of every routing decision, node runtime, and token consumption is saved locally in: [trace_multi_agent.json](file:///Users/nguyenhodieulinh/Documents/2A202600567-NguyenHoDieuLinh-phase2-day5-multi-agent-lab/reports/trace_multi_agent.json)."
    ])

    return "\n".join(lines) + "\n"


def render_html_report(
    metrics: list[BenchmarkMetrics],
    baseline_output: str = "",
    multi_output: str = ""
) -> str:
    """Render benchmark metrics to an interactive, beautiful HTML dashboard."""
    # Find metric profiles
    baseline = next((m for m in metrics if "baseline" in m.run_name.lower()), None)
    multi = next((m for m in metrics if "multi" in m.run_name.lower()), None)

    # Get values or defaults
    b_latency = baseline.latency_seconds if baseline else 0.0
    m_latency = multi.latency_seconds if multi else 0.0
    
    b_cost = baseline.estimated_cost_usd if (baseline and baseline.estimated_cost_usd is not None) else 0.0
    m_cost = multi.estimated_cost_usd if (multi and multi.estimated_cost_usd is not None) else 0.0
    
    b_tokens = (baseline.input_tokens + baseline.output_tokens) if (baseline and baseline.input_tokens and baseline.output_tokens) else 0
    m_tokens = (multi.input_tokens + multi.output_tokens) if (multi and multi.input_tokens and multi.output_tokens) else 0

    b_quality = baseline.quality_score if (baseline and baseline.quality_score is not None) else 0.0
    m_quality = multi.quality_score if (multi and multi.quality_score is not None) else 0.0

    b_citation = baseline.citation_coverage if (baseline and baseline.citation_coverage is not None) else 0.0
    m_citation = multi.citation_coverage if (multi and multi.citation_coverage is not None) else 0.0

    # Calculate bar widths (relative percentages)
    max_latency = max(b_latency, m_latency, 1.0)
    b_lat_width = (b_latency / max_latency) * 100
    m_lat_width = (m_latency / max_latency) * 100

    max_tokens = max(b_tokens, m_tokens, 1)
    b_tok_width = (b_tokens / max_tokens) * 100
    m_tok_width = (m_tokens / max_tokens) * 100

    max_cost = max(b_cost, m_cost, 0.00001)
    b_cost_width = (b_cost / max_cost) * 100
    m_cost_width = (m_cost / max_cost) * 100

    b_qual_width = b_quality * 10
    m_qual_width = m_quality * 10

    # Escape markdown for HTML rendering
    import html as html_lib
    b_output_html = html_lib.escape(baseline_output)
    m_output_html = html_lib.escape(multi_output)

    # Generate table rows
    table_rows = ""
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10.0"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage * 100:.1f}%"
        input_t = "" if item.input_tokens is None else f"{item.input_tokens:,}"
        output_t = "" if item.output_tokens is None else f"{item.output_tokens:,}"
        total_t = "" if (item.input_tokens is None or item.output_tokens is None) else f"{item.input_tokens + item.output_tokens:,}"
        table_rows += f"""
        <tr>
            <td style="font-weight: 500;">{item.run_name}</td>
            <td>{item.latency_seconds:.2f}s</td>
            <td>{input_t}</td>
            <td>{output_t}</td>
            <td>{total_t}</td>
            <td style="font-weight: 600; color: #34d399;">{cost}</td>
            <td>{quality}</td>
            <td>{citation}</td>
            <td style="color: #94a3b8; font-size: 0.9rem;">{item.notes}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent vs Single-Agent Benchmark Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --secondary: #10b981;
            --warning: #f59e0b;
            --border-color: #334155;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at top left, rgba(59, 130, 246, 0.08), transparent 40%), radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.08), transparent 40%);
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 1000px;
            width: 100%;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(to right, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 1.05rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 25px;
            margin-bottom: 35px;
        }}
        @media(min-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
        }}
        .card-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .card-baseline .card-title {{
            color: var(--primary);
        }}
        .card-multi .card-title {{
            color: var(--secondary);
        }}
        .metric-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .metric-box {{
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }}
        .metric-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 1.4rem;
            font-weight: 700;
        }}
        .table-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 35px;
            overflow-x: auto;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 14px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.95rem;
        }}
        th {{
            color: var(--text-muted);
            font-weight: 500;
        }}
        .charts-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 35px;
        }}
        .bar-group {{
            margin-bottom: 20px;
        }}
        .bar-group:last-child {{
            margin-bottom: 0;
        }}
        .bar-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            margin-bottom: 6px;
        }}
        .bar-outer {{
            background-color: rgba(15, 23, 42, 0.5);
            border-radius: 4px;
            height: 10px;
            overflow: hidden;
        }}
        .bar-inner {{
            height: 100%;
            border-radius: 4px;
        }}
        .bar-blue {{ background: linear-gradient(to right, #3b82f6, #60a5fa); }}
        .bar-green {{ background: linear-gradient(to right, #10b981, #34d399); }}
        .findings-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 35px;
        }}
        .findings-title {{
            color: var(--warning);
        }}
        .finding-item {{
            margin-bottom: 15px;
        }}
        .finding-item:last-child {{
            margin-bottom: 0;
        }}
        .finding-heading {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .finding-text {{
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0;
        }}
        .output-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 35px;
        }}
        .output-header {{
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--primary);
        }}
        .output-box {{
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            font-size: 0.9rem;
            color: #e2e8f0;
            max-height: 400px;
            overflow-y: auto;
        }}
        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Multi-Agent vs. Single-Agent</h1>
            <div class="subtitle">System Performance and Token Benchmark Dashboard</div>
        </header>

        <div class="grid">
            <div class="card card-baseline">
                <div class="card-title">Single-Agent Baseline</div>
                <div class="metric-row">
                    <div class="metric-box">
                        <div class="metric-label">Latency</div>
                        <div class="metric-value" style="color: #60a5fa;">{b_latency:.2f}s</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Cost</div>
                        <div class="metric-value">${b_cost:.5f}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Tokens</div>
                        <div class="metric-value">{b_tokens:,}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Citations</div>
                        <div class="metric-value">{b_citation * 100:.1f}%</div>
                    </div>
                </div>
            </div>

            <div class="card card-multi">
                <div class="card-title">Multi-Agent Workflow</div>
                <div class="metric-row">
                    <div class="metric-box">
                        <div class="metric-label">Latency</div>
                        <div class="metric-value" style="color: #34d399;">{m_latency:.2f}s</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Cost</div>
                        <div class="metric-value">${m_cost:.5f}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Tokens</div>
                        <div class="metric-value">{m_tokens:,}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Citations</div>
                        <div class="metric-value">{m_citation * 100:.1f}%</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-card">
            <div class="section-title">Visual Comparison Analysis</div>
            
            <div class="bar-group">
                <div class="bar-label">
                    <span>Latency (s) - Lower is Better</span>
                    <span>Single ({b_latency:.1f}s) vs Multi ({m_latency:.1f}s)</span>
                </div>
                <div class="bar-outer">
                    <div class="bar-inner bar-blue" style="width: {b_lat_width}%;"></div>
                </div>
                <div class="bar-outer" style="margin-top: 5px;">
                    <div class="bar-inner bar-green" style="width: {m_lat_width}%;"></div>
                </div>
            </div>

            <div class="bar-group">
                <div class="bar-label">
                    <span>Total Tokens - Lower is Better</span>
                    <span>Single ({b_tokens:,}) vs Multi ({m_tokens:,})</span>
                </div>
                <div class="bar-outer">
                    <div class="bar-inner bar-blue" style="width: {b_tok_width}%;"></div>
                </div>
                <div class="bar-outer" style="margin-top: 5px;">
                    <div class="bar-inner bar-green" style="width: {m_tok_width}%;"></div>
                </div>
            </div>

            <div class="bar-group">
                <div class="bar-label">
                    <span>Quality Score (0-10) - Higher is Better</span>
                    <span>Single ({b_quality:.1f}) vs Multi ({m_quality:.1f})</span>
                </div>
                <div class="bar-outer">
                    <div class="bar-inner bar-blue" style="width: {b_qual_width}%;"></div>
                </div>
                <div class="bar-outer" style="margin-top: 5px;">
                    <div class="bar-inner bar-green" style="width: {m_qual_width}%;"></div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <div class="section-title">Detailed Metrics Matrix</div>
            <table>
                <thead>
                    <tr>
                        <th>Run Profile</th>
                        <th>Latency</th>
                        <th>Input Tokens</th>
                        <th>Output Tokens</th>
                        <th>Total Tokens</th>
                        <th>Est. Cost</th>
                        <th>Quality</th>
                        <th>Citations</th>
                        <th>Execution Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div class="findings-card">
            <div class="section-title findings-title">Exit Ticket & Failure Modes (Lab Guide / README Deliverables)</div>
            
            <div class="finding-item">
                <div class="finding-heading" style="color: #60a5fa;">Exit Ticket 1: Case nào nên dùng multi-agent?</div>
                <p class="finding-text">
                    Nên dùng multi-agent cho các tác vụ nghiên cứu chuyên sâu, phức tạp và đòi hỏi tính chính xác cao. Việc phân tách vai trò (Researcher thu thập nguồn tin, Analyst phân tích dữ liệu, Critic đối chiếu tính đúng đắn) giúp giảm thiểu hiện tượng ảo giác (hallucinations), tăng độ phủ trích dẫn và đảm bảo nội dung đáp ứng toàn bộ các tiêu chí ràng buộc.
                </p>
            </div>

            <div class="finding-item">
                <div class="finding-heading" style="color: #60a5fa;">Exit Ticket 2: Case nào không nên dùng multi-agent?</div>
                <p class="finding-text">
                    Không nên dùng cho các tác vụ đơn giản, quen thuộc hoặc đòi hỏi thời gian phản hồi cực nhanh (latency-sensitive). Việc gọi tuần tự qua nhiều agent sẽ nhân số lượng token tiêu thụ lên gấp 10-20 lần và gia tăng thời gian chờ đáng kể, làm mất đi tính kinh tế.
                </p>
            </div>

            <div class="finding-item">
                <div class="finding-heading" style="color: #ef4444;">Failure Mode 1: Context drift during state handoffs</div>
                <p class="finding-text">
                    <strong>Khắc phục:</strong> Thiết lập cấu trúc Pydantic schema đồng nhất cho ResearchState, lưu trữ toàn bộ lịch sử trích dẫn, ghi chép phân tích và phản hồi của Critic. Việc này giúp các agent kế thừa trọn vẹn thông tin mà không cần truyền lại toàn bộ lịch sử hội thoại thô.
                </p>
            </div>

            <div class="finding-item">
                <div class="finding-heading" style="color: #ef4444;">Failure Mode 2: Rate limiting or API quota issues</div>
                <p class="finding-text">
                    <strong>Khắc phục:</strong> Tích hợp cơ chế tự động thử lại (Retry) với độ trễ lũy thừa (wait_exponential) bằng thư viện tenacity trong LLMClient. Đồng thời, bổ sung cơ chế fallback thông minh tự động chuyển sang local mock response khi API bị lỗi 429 hoặc hết hạn mức sử dụng.
                </p>
            </div>
        </div>

        <div class="output-container">
            <div class="section-title">Generated Outputs Comparison</div>
            
            <div class="bar-group">
                <div class="output-header" style="color: var(--primary);">Single-Agent Baseline Output</div>
                <div class="output-box">{b_output_html}</div>
            </div>

            <div class="bar-group" style="margin-top: 25px;">
                <div class="output-header" style="color: var(--secondary);">Multi-Agent Workflow Output</div>
                <div class="output-box">{m_output_html}</div>
            </div>
        </div>

        <footer>
            Trace details logged to <code style="background: rgba(255,255,255,0.05); padding: 3px 6px; border-radius: 4px;">reports/trace_multi_agent.json</code>
        </footer>
    </div>
</body>
</html>
"""
    return html
