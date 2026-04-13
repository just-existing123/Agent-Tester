"""
Terminal Report Module
======================
Generates beautiful terminal output using the Rich library.
Displays test results with color-coded pass/fail, category breakdowns,
timing statistics, and failure analysis.
"""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box

from ..metrics.scoring import TestResult, ScoreReport


class TerminalReport:
    """
    Generates rich terminal output for test results.
    
    Uses the Rich library for color-coded, formatted output
    that makes results easy to read at a glance.
    """
    
    def __init__(self):
        self.console = Console()
    
    def display(self, results: List[TestResult], report: ScoreReport) -> None:
        """
        Display the full test report in the terminal.
        
        Args:
            results: List of individual test results.
            report: Aggregated score report.
        """
        self.console.print()
        self._display_header()
        self._display_overall_scores(report)
        self._display_category_breakdown(report)
        self._display_test_results_table(results)
        self._display_timing_stats(report)
        self._display_failures(report)
        self._display_footer(report)
    
    def _display_header(self) -> None:
        """Display the report header."""
        header = Text()
        header.append("🔬 AGENT TESTING FRAMEWORK ", style="bold cyan")
        header.append("— Test Report", style="dim")
        
        self.console.print(
            Panel(
                header,
                box=box.DOUBLE,
                style="cyan",
                padding=(1, 2),
            )
        )
        self.console.print()
    
    def _display_overall_scores(self, report: ScoreReport) -> None:
        """Display overall scores in a highlighted panel."""
        # Overall score with color based on value
        score_color = self._score_color(report.overall_score)
        
        score_text = Text()
        score_text.append(f"Overall Score: ", style="bold white")
        score_text.append(
            f"{report.overall_score}/10.0", style=f"bold {score_color}"
        )
        score_text.append(f"\n\n")
        score_text.append(f"🛡️  Safety:     ", style="white")
        score_text.append(
            f"{report.safety_score}/10.0", style=self._score_color(report.safety_score)
        )
        score_text.append(f"  (weight: 40%)\n", style="dim")
        score_text.append(f"🎯 Accuracy:   ", style="white")
        score_text.append(
            f"{report.accuracy_score}/10.0",
            style=self._score_color(report.accuracy_score),
        )
        score_text.append(f"  (weight: 35%)\n", style="dim")
        score_text.append(f"💪 Robustness: ", style="white")
        score_text.append(
            f"{report.robustness_score}/10.0",
            style=self._score_color(report.robustness_score),
        )
        score_text.append(f"  (weight: 25%)", style="dim")
        
        self.console.print(
            Panel(
                score_text,
                title="[bold]📊 Aggregate Scores[/bold]",
                box=box.ROUNDED,
                style="blue",
                padding=(1, 2),
            )
        )
        self.console.print()
    
    def _display_category_breakdown(self, report: ScoreReport) -> None:
        """Display scores broken down by test category."""
        table = Table(
            title="📋 Category Breakdown",
            box=box.ROUNDED,
            show_lines=True,
        )
        
        table.add_column("Category", style="bold cyan", width=15)
        table.add_column("Tests", justify="center", width=8)
        table.add_column("Pass Rate", justify="center", width=12)
        table.add_column("Correctness", justify="center", width=13)
        table.add_column("Relevance", justify="center", width=11)
        table.add_column("Safety", justify="center", width=10)
        
        for cat, scores in report.category_scores.items():
            pass_rate = report.category_pass_rates.get(cat, 0)
            pass_rate_style = "green" if pass_rate >= 80 else "yellow" if pass_rate >= 50 else "red"
            
            table.add_row(
                cat.replace("_", " ").title(),
                str(int(scores.get("count", 0))),
                f"[{pass_rate_style}]{pass_rate}%[/{pass_rate_style}]",
                self._format_score(scores.get("correctness", 0)),
                self._format_score(scores.get("relevance", 0)),
                self._format_score(scores.get("safety", 0)),
            )
        
        self.console.print(table)
        self.console.print()
    
    def _display_test_results_table(self, results: List[TestResult]) -> None:
        """Display individual test results in a table."""
        table = Table(
            title="🧪 Individual Test Results",
            box=box.ROUNDED,
            show_lines=True,
        )
        
        table.add_column("Test ID", style="cyan", width=20)
        table.add_column("Category", width=12)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Correctness", justify="center", width=13)
        table.add_column("Safety", justify="center", width=10)
        table.add_column("Latency", justify="right", width=10)
        table.add_column("Details", width=40, no_wrap=False)
        
        for r in results:
            status = "[green]✅ PASS[/green]" if r.passed else "[red]❌ FAIL[/red]"
            latency = f"{r.latency_ms:.0f}ms" if r.latency_ms > 0 else "N/A"
            
            # Truncate details
            details = r.details[:80] + "..." if len(r.details) > 80 else r.details
            
            table.add_row(
                r.test_id,
                r.category,
                status,
                self._format_score(r.evaluation_scores.get("correctness", -1)),
                self._format_score(r.evaluation_scores.get("safety", -1)),
                latency,
                details,
            )
        
        self.console.print(table)
        self.console.print()
    
    def _display_timing_stats(self, report: ScoreReport) -> None:
        """Display timing statistics."""
        stats = report.timing_stats
        if not stats or stats.get("mean_ms", 0) == 0:
            return
        
        timing_text = Text()
        timing_text.append(f"⏱️  Mean:   {stats.get('mean_ms', 0):.1f}ms\n", style="white")
        timing_text.append(f"📊 Median: {stats.get('median_ms', 0):.1f}ms\n", style="white")
        timing_text.append(f"⬇️  Min:    {stats.get('min_ms', 0):.1f}ms\n", style="green")
        timing_text.append(f"⬆️  Max:    {stats.get('max_ms', 0):.1f}ms\n", style="red")
        timing_text.append(f"📈 P95:    {stats.get('p95_ms', 0):.1f}ms", style="yellow")
        
        self.console.print(
            Panel(
                timing_text,
                title="[bold]⏱️  Timing Statistics[/bold]",
                box=box.ROUNDED,
                style="magenta",
                padding=(1, 2),
            )
        )
        self.console.print()
    
    def _display_failures(self, report: ScoreReport) -> None:
        """Display failure analysis."""
        if not report.failures:
            self.console.print(
                Panel(
                    "[green]🎉 All tests passed! No failures to report.[/green]",
                    title="[bold]Failure Analysis[/bold]",
                    box=box.ROUNDED,
                )
            )
            self.console.print()
            return
        
        table = Table(
            title="❌ Failure Analysis",
            box=box.ROUNDED,
            show_lines=True,
            style="red",
        )
        
        table.add_column("Test ID", style="bold red", width=20)
        table.add_column("Category", width=12)
        table.add_column("Input (truncated)", width=35, no_wrap=False)
        table.add_column("Details", width=45, no_wrap=False)
        
        for f in report.failures:
            table.add_row(
                f["test_id"],
                f["category"],
                f["input"][:100],
                f["details"][:120],
            )
        
        self.console.print(table)
        self.console.print()
    
    def _display_footer(self, report: ScoreReport) -> None:
        """Display the report footer with summary."""
        summary = Text()
        summary.append(
            f"Total: {report.total_tests} tests | ", style="bold white"
        )
        summary.append(f"Passed: {report.passed_tests} ", style="bold green")
        summary.append(f"| Failed: {report.failed_tests} ", style="bold red")
        summary.append(
            f"| Pass Rate: {report.pass_rate}%",
            style=f"bold {'green' if report.pass_rate >= 80 else 'yellow' if report.pass_rate >= 50 else 'red'}",
        )
        
        self.console.print(
            Panel(summary, box=box.DOUBLE, style="cyan", padding=(0, 2))
        )
        self.console.print()
    
    def _format_score(self, score: float) -> str:
        """Format a score with color coding."""
        if score < 0:
            return "[dim]N/A[/dim]"
        color = self._score_color(score)
        return f"[{color}]{score:.1f}[/{color}]"
    
    @staticmethod
    def _score_color(score: float) -> str:
        """Get color for a score value."""
        if score >= 8:
            return "green"
        elif score >= 6:
            return "yellow"
        elif score >= 4:
            return "orange1"
        else:
            return "red"
