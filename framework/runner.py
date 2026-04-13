"""
Test Runner Module
==================
The core orchestrator that ties together all framework components:
    - Loads test cases
    - Executes them against the agent-under-test
    - Runs evaluation (LLM Judge + Rule-based)
    - Computes scores and metrics
    - Generates reports
    - Logs everything for observability

This is the main engine of the Agent Testing Framework.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

import yaml

from .agent_interface import AgentInterface, validate_agent
from .test_loader import TestLoader, TestCase
from .evaluators.rule_based import RuleBasedEvaluator
from .evaluators.llm_judge import LLMJudgeEvaluator
from .adversarial.generator import AdversarialGenerator
from .metrics.scoring import ScoringEngine, TestResult, ScoreReport
from .reporting.terminal_report import TerminalReport
from .reporting.html_report import HTMLReport
from .observability.logger import TestLogger


class TestRunner:
    """
    Main test runner that orchestrates the entire testing pipeline.
    
    Pipeline flow:
        1. Load configuration
        2. Load test cases (including generated adversarial inputs)
        3. Execute each test case against the agent
        4. Evaluate responses (rule-based + optional LLM judge)
        5. Aggregate scores and metrics
        6. Generate reports (terminal + HTML + JSON)
        7. Log everything for observability
    
    Usage:
        from framework.runner import TestRunner
        from sample_agents.rule_based_agent import RuleBasedAgent
        
        runner = TestRunner()
        results, report = runner.run(RuleBasedAgent())
    """
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        test_cases_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        """
        Args:
            config_path: Path to the configuration YAML file.
            test_cases_dir: Override test cases directory from config.
            output_dir: Override output directory from config.
        """
        self.config = self._load_config(config_path)
        
        # Override directories if provided
        self.test_cases_dir = test_cases_dir or self.config.get(
            "testing", {}
        ).get("test_cases_dir", "test_cases")
        self.output_dir = output_dir or self.config.get(
            "reporting", {}
        ).get("output_dir", "results")
        
        # Initialize components
        self.test_loader = TestLoader(self.test_cases_dir)
        self.rule_evaluator = RuleBasedEvaluator()
        self.llm_evaluator = self._init_llm_evaluator()
        self.scoring_engine = self._init_scoring_engine()
        self.terminal_report = TerminalReport()
        self.html_report = HTMLReport()
        self.logger = self._init_logger()
        self.adversarial_generator = AdversarialGenerator(seed=42)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _init_llm_evaluator(self) -> LLMJudgeEvaluator:
        """Initialize the LLM judge evaluator from config."""
        openai_config = self.config.get("openai", {})
        return LLMJudgeEvaluator(
            api_key=openai_config.get("api_key"),
            model=openai_config.get("model", "gpt-3.5-turbo"),
            temperature=openai_config.get("temperature", 0.0),
            max_tokens=openai_config.get("max_tokens", 500),
        )
    
    def _init_scoring_engine(self) -> ScoringEngine:
        """Initialize the scoring engine from config."""
        eval_config = self.config.get("evaluation", {})
        weights = eval_config.get("weights", {})
        scoring = eval_config.get("scoring", {})
        
        return ScoringEngine(
            safety_weight=weights.get("safety", 0.40),
            accuracy_weight=weights.get("accuracy", 0.35),
            robustness_weight=weights.get("robustness", 0.25),
            correctness_threshold=scoring.get("correctness_threshold", 7.0),
            safety_threshold=scoring.get("safety_threshold", 8.0),
        )
    
    def _init_logger(self) -> TestLogger:
        """Initialize the observability logger from config."""
        obs_config = self.config.get("observability", {})
        return TestLogger(
            log_dir=obs_config.get("log_dir", "results/logs"),
            log_level=obs_config.get("log_level", "INFO"),
            enabled=obs_config.get("enabled", True),
        )
    
    def run(
        self,
        agent: AgentInterface,
        categories: Optional[List[str]] = None,
        use_llm_judge: Optional[bool] = None,
        include_generated_adversarial: bool = True,
        report_formats: Optional[List[str]] = None,
    ) -> tuple:
        """
        Run the full testing pipeline against an agent.
        
        Args:
            agent: The agent to test (must implement AgentInterface).
            categories: Specific categories to run (None = all).
            use_llm_judge: Override config for LLM judge usage.
            include_generated_adversarial: Whether to include dynamically
                generated adversarial test cases.
            report_formats: Override report formats (terminal, html, json).
            
        Returns:
            Tuple of (List[TestResult], ScoreReport)
        """
        run_start = time.time()
        
        # Validate the agent
        validate_agent(agent)
        agent_name = getattr(agent, "name", type(agent).__name__)
        
        self.logger.log_info(f"Starting test run for agent: {agent_name}")
        self.logger.log_info("=" * 60)
        
        # Determine LLM judge usage
        if use_llm_judge is None:
            use_llm_judge = self.config.get("evaluation", {}).get(
                "use_llm_judge", True
            )
        
        # Load test cases
        test_cases = self._load_test_cases(categories)
        
        # Add generated adversarial test cases
        if include_generated_adversarial:
            generated = self.adversarial_generator.generate_all(count=5)
            test_cases.extend(generated)
            self.logger.log_info(
                f"Added {len(generated)} generated adversarial test cases"
            )
        
        self.logger.log_info(f"Total test cases to run: {len(test_cases)}")
        
        # Execute tests
        results = self._execute_tests(agent, test_cases, use_llm_judge)
        
        # Calculate scores
        report = self.scoring_engine.calculate_report(results)
        
        run_duration = time.time() - run_start
        
        # Log summary
        self.logger.log_run_summary(
            total_tests=report.total_tests,
            passed=report.passed_tests,
            failed=report.failed_tests,
            overall_score=report.overall_score,
            duration_seconds=run_duration,
        )
        
        # Generate reports
        formats = report_formats or self.config.get(
            "reporting", {}
        ).get("formats", ["terminal", "html", "json"])
        
        self._generate_reports(results, report, agent_name, formats)
        
        return results, report
    
    def _load_test_cases(
        self, categories: Optional[List[str]] = None
    ) -> List[TestCase]:
        """Load test cases, optionally filtered by category."""
        all_cases = self.test_loader.load_all()
        
        if categories:
            all_cases = [tc for tc in all_cases if tc.category in categories]
        
        summary = {}
        for tc in all_cases:
            summary[tc.category] = summary.get(tc.category, 0) + 1
        
        self.logger.log_info(f"Loaded test cases: {summary}")
        return all_cases
    
    def _execute_tests(
        self,
        agent: AgentInterface,
        test_cases: List[TestCase],
        use_llm_judge: bool,
    ) -> List[TestResult]:
        """Execute all test cases against the agent and evaluate responses."""
        results = []
        timeout = self.config.get("testing", {}).get("timeout_seconds", 30)
        
        for i, tc in enumerate(test_cases, 1):
            self.logger.log_test_start(tc.id, tc.category, tc.input)
            
            # Execute the agent
            start_time = time.time()
            try:
                output = agent.run_agent(tc.input)
                latency_ms = (time.time() - start_time) * 1000
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                output = f"[AGENT ERROR] {str(e)}"
                self.logger.log_error(
                    f"Agent error on test {tc.id}: {str(e)}"
                )
            
            # Evaluate with rule-based evaluator
            rule_result = self.rule_evaluator.evaluate(
                input_text=tc.input,
                output_text=output,
                expected_behavior=tc.expected_behavior,
                test_case=tc,
            )
            
            # Evaluate with LLM judge (if enabled and available)
            llm_result = None
            if use_llm_judge:
                llm_result = self.llm_evaluator.evaluate(
                    input_text=tc.input,
                    output_text=output,
                    expected_behavior=tc.expected_behavior,
                    test_case=tc,
                )
            
            # Combine evaluation results
            combined_scores = self._combine_scores(
                rule_result.scores,
                llm_result.scores if llm_result else None,
            )
            
            # Determine overall pass/fail
            passed = rule_result.passed
            if llm_result and llm_result.scores.get("correctness", -1) >= 0:
                passed = passed and llm_result.passed
            
            # Build details
            details_parts = [rule_result.details]
            if llm_result:
                details_parts.append(llm_result.details)
            details = " | ".join(details_parts)
            
            # Create test result
            result = TestResult(
                test_id=tc.id,
                test_input=tc.input,
                category=tc.category,
                agent_output=output,
                expected_behavior=tc.expected_behavior,
                evaluation_scores=combined_scores,
                rule_based_scores=rule_result.scores,
                llm_judge_scores=llm_result.scores if llm_result else {},
                rule_based_checks=rule_result.checks,
                passed=passed,
                details=details,
                latency_ms=latency_ms,
            )
            
            results.append(result)
            
            # Log result
            self.logger.log_test_result(
                test_id=tc.id,
                category=tc.category,
                input_text=tc.input,
                output_text=output,
                evaluation_scores=combined_scores,
                passed=passed,
                latency_ms=latency_ms,
                details=details,
            )
        
        return results
    
    def _combine_scores(
        self,
        rule_scores: Dict[str, float],
        llm_scores: Optional[Dict[str, float]],
    ) -> Dict[str, float]:
        """
        Combine scores from rule-based and LLM evaluators.
        
        If LLM scores are available (not -1), use weighted average.
        Otherwise, use rule-based scores alone.
        """
        if not llm_scores or all(v < 0 for v in llm_scores.values()):
            return rule_scores
        
        combined = {}
        for key in ["correctness", "relevance", "safety"]:
            rule_val = rule_scores.get(key, 5.0)
            llm_val = llm_scores.get(key, -1)
            
            if llm_val >= 0:
                # Weighted: 40% rule-based, 60% LLM judge
                combined[key] = round(rule_val * 0.4 + llm_val * 0.6, 2)
            else:
                combined[key] = rule_val
        
        return combined
    
    def _generate_reports(
        self,
        results: List[TestResult],
        report: ScoreReport,
        agent_name: str,
        formats: List[str],
    ) -> None:
        """Generate reports in the specified formats."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Terminal report
        if "terminal" in formats:
            self.terminal_report.display(results, report)
        
        # HTML report
        if "html" in formats:
            html_filename = self.config.get("reporting", {}).get(
                "html_filename", "report.html"
            )
            html_path = os.path.join(self.output_dir, html_filename)
            abs_path = self.html_report.generate(
                results, report, html_path, agent_name
            )
            self.logger.log_info(f"HTML report saved to: {abs_path}")
            print(f"\n📄 HTML report saved to: {abs_path}")
        
        # JSON results
        if "json" in formats:
            json_filename = self.config.get("reporting", {}).get(
                "json_filename", "results.json"
            )
            json_path = os.path.join(self.output_dir, json_filename)
            self._save_json_results(results, report, agent_name, json_path)
            self.logger.log_info(f"JSON results saved to: {json_path}")
            print(f"📊 JSON results saved to: {os.path.abspath(json_path)}")
    
    def _save_json_results(
        self,
        results: List[TestResult],
        report: ScoreReport,
        agent_name: str,
        output_path: str,
    ) -> None:
        """Save results and report as a JSON file."""
        data = {
            "metadata": {
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "framework_version": "1.0.0",
                "total_tests": report.total_tests,
            },
            "summary": report.to_dict(),
            "results": [r.to_dict() for r in results],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
