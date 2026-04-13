"""
HTML Report Module
==================
Generates a self-contained HTML report with embedded CSS and Chart.js.
The report includes executive summary, score charts, detailed results,
failure analysis, and timing breakdown.
"""

import json
import os
from datetime import datetime
from typing import List

from ..metrics.scoring import TestResult, ScoreReport


class HTMLReport:
    """
    Generates a self-contained HTML report file.
    
    Features:
        - Executive summary with overall scores
        - Interactive charts (Chart.js)
        - Per-test-case detailed results
        - Failure analysis section
        - Timing breakdown
    """
    
    def generate(
        self,
        results: List[TestResult],
        report: ScoreReport,
        output_path: str = "results/report.html",
        agent_name: str = "Unknown Agent",
    ) -> str:
        """
        Generate an HTML report and save it to disk.
        
        Args:
            results: List of individual test results.
            report: Aggregated score report.
            output_path: Path to save the HTML file.
            agent_name: Name of the agent being tested.
            
        Returns:
            Absolute path to the generated report.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        html = self._build_html(results, report, agent_name)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return os.path.abspath(output_path)
    
    def _build_html(
        self,
        results: List[TestResult],
        report: ScoreReport,
        agent_name: str,
    ) -> str:
        """Build the complete HTML document."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare chart data
        categories = list(report.category_scores.keys())
        cat_correctness = [report.category_scores[c].get("correctness", 0) for c in categories]
        cat_relevance = [report.category_scores[c].get("relevance", 0) for c in categories]
        cat_safety = [report.category_scores[c].get("safety", 0) for c in categories]
        cat_pass_rates = [report.category_pass_rates.get(c, 0) for c in categories]
        
        # Build results rows
        results_rows = ""
        for r in results:
            status_class = "pass" if r.passed else "fail"
            status_text = "✅ PASS" if r.passed else "❌ FAIL"
            correctness = r.evaluation_scores.get("correctness", -1)
            safety = r.evaluation_scores.get("safety", -1)
            latency = f"{r.latency_ms:.0f}ms" if r.latency_ms > 0 else "N/A"
            details_escaped = r.details.replace("<", "&lt;").replace(">", "&gt;")[:150]
            input_escaped = r.test_input.replace("<", "&lt;").replace(">", "&gt;")[:100]
            output_escaped = r.agent_output.replace("<", "&lt;").replace(">", "&gt;")[:150]
            
            results_rows += f"""
            <tr class="{status_class}">
                <td><strong>{r.test_id}</strong></td>
                <td>{r.category}</td>
                <td class="status-{status_class}">{status_text}</td>
                <td>{self._format_score_html(correctness)}</td>
                <td>{self._format_score_html(safety)}</td>
                <td>{latency}</td>
                <td class="details-cell" title="{details_escaped}">{details_escaped}</td>
            </tr>
            """
        
        # Build failures rows
        failures_rows = ""
        for f in report.failures:
            input_escaped = f["input"].replace("<", "&lt;").replace(">", "&gt;")
            details_escaped = f["details"].replace("<", "&lt;").replace(">", "&gt;")
            failures_rows += f"""
            <tr>
                <td><strong>{f['test_id']}</strong></td>
                <td>{f['category']}</td>
                <td>{input_escaped}</td>
                <td>{details_escaped}</td>
            </tr>
            """
        
        if not failures_rows:
            failures_rows = """
            <tr>
                <td colspan="4" style="text-align: center; color: #4ade80;">
                    🎉 All tests passed! No failures to report.
                </td>
            </tr>
            """
        
        timing = report.timing_stats
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Testing Report — {agent_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --accent-yellow: #fbbf24;
            --accent-purple: #a78bfa;
            --border: #334155;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #1e3a5f, #0f172a);
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }}
        
        .header h1 {{
            font-size: 2rem;
            background: linear-gradient(120deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header .meta {{ color: var(--text-secondary); margin-top: 0.5rem; }}
        
        .score-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .score-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s;
        }}
        
        .score-card:hover {{ transform: translateY(-2px); }}
        
        .score-card .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .score-card .value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }}
        
        .score-card .subtitle {{ font-size: 0.8rem; color: var(--text-secondary); }}
        
        .score-green {{ color: var(--accent-green); }}
        .score-yellow {{ color: var(--accent-yellow); }}
        .score-red {{ color: var(--accent-red); }}
        
        .section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .section h2 {{
            font-size: 1.3rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .chart-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        th {{
            background: var(--bg-primary);
            color: var(--text-secondary);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}
        
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}
        
        tr:hover {{ background: rgba(59, 130, 246, 0.05); }}
        
        .status-pass {{ color: var(--accent-green); font-weight: bold; }}
        .status-fail {{ color: var(--accent-red); font-weight: bold; }}
        
        .details-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .timing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }}
        
        .timing-item {{
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        
        .timing-item .label {{ font-size: 0.8rem; color: var(--text-secondary); }}
        .timing-item .value {{ font-size: 1.5rem; font-weight: bold; color: var(--accent-blue); }}
        
        .footer {{
            text-align: center;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔬 Agent Testing Framework Report</h1>
            <p class="meta">Agent: <strong>{agent_name}</strong> | Generated: {timestamp}</p>
        </div>
        
        <!-- Score Cards -->
        <div class="score-cards">
            <div class="score-card">
                <div class="label">Overall Score</div>
                <div class="value {self._score_class(report.overall_score)}">{report.overall_score}</div>
                <div class="subtitle">out of 10.0</div>
            </div>
            <div class="score-card">
                <div class="label">🛡️ Safety</div>
                <div class="value {self._score_class(report.safety_score)}">{report.safety_score}</div>
                <div class="subtitle">Weight: 40%</div>
            </div>
            <div class="score-card">
                <div class="label">🎯 Accuracy</div>
                <div class="value {self._score_class(report.accuracy_score)}">{report.accuracy_score}</div>
                <div class="subtitle">Weight: 35%</div>
            </div>
            <div class="score-card">
                <div class="label">💪 Robustness</div>
                <div class="value {self._score_class(report.robustness_score)}">{report.robustness_score}</div>
                <div class="subtitle">Weight: 25%</div>
            </div>
            <div class="score-card">
                <div class="label">Pass Rate</div>
                <div class="value {self._score_class(report.pass_rate / 10)}">{report.pass_rate}%</div>
                <div class="subtitle">{report.passed_tests}/{report.total_tests} passed</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-container">
                <canvas id="categoryChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="passRateChart"></canvas>
            </div>
        </div>
        
        <!-- Test Results Table -->
        <div class="section">
            <h2>🧪 Detailed Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test ID</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Correctness</th>
                        <th>Safety</th>
                        <th>Latency</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {results_rows}
                </tbody>
            </table>
        </div>
        
        <!-- Timing Statistics -->
        <div class="section">
            <h2>⏱️ Timing Statistics</h2>
            <div class="timing-grid">
                <div class="timing-item">
                    <div class="label">Mean</div>
                    <div class="value">{timing.get('mean_ms', 0):.1f}ms</div>
                </div>
                <div class="timing-item">
                    <div class="label">Median</div>
                    <div class="value">{timing.get('median_ms', 0):.1f}ms</div>
                </div>
                <div class="timing-item">
                    <div class="label">Min</div>
                    <div class="value">{timing.get('min_ms', 0):.1f}ms</div>
                </div>
                <div class="timing-item">
                    <div class="label">Max</div>
                    <div class="value">{timing.get('max_ms', 0):.1f}ms</div>
                </div>
                <div class="timing-item">
                    <div class="label">P95</div>
                    <div class="value">{timing.get('p95_ms', 0):.1f}ms</div>
                </div>
            </div>
        </div>
        
        <!-- Failure Analysis -->
        <div class="section">
            <h2>❌ Failure Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test ID</th>
                        <th>Category</th>
                        <th>Input</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {failures_rows}
                </tbody>
            </table>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated by Agent Testing Framework v1.0.0 | {timestamp}</p>
        </div>
    </div>
    
    <script>
        // Category Scores Chart
        new Chart(document.getElementById('categoryChart'), {{
            type: 'radar',
            data: {{
                labels: {json.dumps([c.replace('_', ' ').title() for c in categories])},
                datasets: [
                    {{
                        label: 'Correctness',
                        data: {json.dumps(cat_correctness)},
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        pointBackgroundColor: '#3b82f6',
                    }},
                    {{
                        label: 'Safety',
                        data: {json.dumps(cat_safety)},
                        borderColor: '#4ade80',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)',
                        pointBackgroundColor: '#4ade80',
                    }},
                    {{
                        label: 'Relevance',
                        data: {json.dumps(cat_relevance)},
                        borderColor: '#a78bfa',
                        backgroundColor: 'rgba(167, 139, 250, 0.1)',
                        pointBackgroundColor: '#a78bfa',
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ title: {{ display: true, text: 'Scores by Category', color: '#f8fafc' }} }},
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 10,
                        ticks: {{ color: '#94a3b8' }},
                        grid: {{ color: '#334155' }},
                        pointLabels: {{ color: '#f8fafc' }}
                    }}
                }}
            }}
        }});
        
        // Pass Rate Chart
        new Chart(document.getElementById('passRateChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([c.replace('_', ' ').title() for c in categories])},
                datasets: [{{
                    label: 'Pass Rate (%)',
                    data: {json.dumps(cat_pass_rates)},
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(167, 139, 250, 0.7)',
                        'rgba(251, 191, 36, 0.7)',
                        'rgba(74, 222, 128, 0.7)',
                    ],
                    borderColor: [
                        '#3b82f6',
                        '#a78bfa',
                        '#fbbf24',
                        '#4ade80',
                    ],
                    borderWidth: 1,
                    borderRadius: 8,
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ title: {{ display: true, text: 'Pass Rate by Category', color: '#f8fafc' }} }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{ color: '#94a3b8' }},
                        grid: {{ color: '#334155' }}
                    }},
                    x: {{
                        ticks: {{ color: '#f8fafc' }},
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    def _format_score_html(self, score: float) -> str:
        """Format a score with color class."""
        if score < 0:
            return '<span style="color: #94a3b8;">N/A</span>'
        css_class = self._score_class(score)
        return f'<span class="{css_class}">{score:.1f}</span>'
    
    @staticmethod
    def _score_class(score: float) -> str:
        """Get CSS class for a score value."""
        if score >= 8:
            return "score-green"
        elif score >= 6:
            return "score-yellow"
        else:
            return "score-red"
