"""
Observability Logger Module
============================
Provides structured JSON logging for all test executions.

Logs capture:
    - Inputs sent to the agent
    - Outputs received from the agent
    - Evaluation scores from all evaluators
    - Timing information
    - Pass/fail status

All logs are written as newline-delimited JSON (NDJSON) for easy
parsing and querying.
"""

import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class TestLogger:
    """
    Structured logger for test execution observability.
    
    Writes logs in two formats:
        1. Human-readable logs via Python logging
        2. Structured JSON logs (NDJSON) for machine consumption
    
    Each test execution is logged as a single JSON object containing
    the input, output, scores, timing, and pass/fail status.
    """
    
    def __init__(
        self,
        log_dir: str = "results/logs",
        log_level: str = "INFO",
        enabled: bool = True,
    ):
        """
        Args:
            log_dir: Directory to write log files.
            log_level: Python logging level (DEBUG, INFO, WARNING, ERROR).
            enabled: Whether logging is enabled.
        """
        self.log_dir = log_dir
        self.enabled = enabled
        self._json_log_path = None
        self._logger = None
        
        if self.enabled:
            self._setup(log_level)
    
    def _setup(self, log_level: str) -> None:
        """Set up logging infrastructure."""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Timestamp for log file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON log file (NDJSON format)
        self._json_log_path = os.path.join(
            self.log_dir, f"test_run_{timestamp}.jsonl"
        )
        
        # Python logger for human-readable output
        self._logger = logging.getLogger("agent_testing")
        self._logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f"test_run_{timestamp}.log"),
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        
        # Avoid duplicate handlers if re-initialized
        if not self._logger.handlers:
            self._logger.addHandler(file_handler)
    
    def log_test_start(self, test_id: str, category: str, input_text: str) -> None:
        """Log the start of a test case execution."""
        if not self.enabled:
            return
        
        self._logger.info(
            f"[START] Test: {test_id} | Category: {category} | "
            f"Input: {input_text[:100]}..."
        )
    
    def log_test_result(
        self,
        test_id: str,
        category: str,
        input_text: str,
        output_text: str,
        evaluation_scores: Dict[str, float],
        passed: bool,
        latency_ms: float,
        details: str = "",
        error: Optional[str] = None,
    ) -> None:
        """
        Log the complete result of a test case execution.
        
        This writes both a human-readable log entry and a structured
        JSON log entry.
        """
        if not self.enabled:
            return
        
        # Human-readable log
        status = "PASS ✅" if passed else "FAIL ❌"
        self._logger.info(
            f"[{status}] Test: {test_id} | Category: {category} | "
            f"Scores: {evaluation_scores} | Latency: {latency_ms:.0f}ms"
        )
        
        if error:
            self._logger.error(f"[ERROR] Test: {test_id} | Error: {error}")
        
        if not passed:
            self._logger.warning(
                f"[FAILURE] Test: {test_id} | Details: {details[:200]}"
            )
        
        # Structured JSON log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "test_id": test_id,
            "category": category,
            "input": input_text,
            "output": output_text,
            "evaluation_scores": evaluation_scores,
            "passed": passed,
            "latency_ms": round(latency_ms, 2),
            "details": details,
            "error": error,
        }
        
        self._write_json_log(log_entry)
    
    def log_run_summary(
        self,
        total_tests: int,
        passed: int,
        failed: int,
        overall_score: float,
        duration_seconds: float,
    ) -> None:
        """Log a summary of the entire test run."""
        if not self.enabled:
            return
        
        self._logger.info("=" * 60)
        self._logger.info(
            f"[SUMMARY] Total: {total_tests} | Passed: {passed} | "
            f"Failed: {failed} | Score: {overall_score}/10 | "
            f"Duration: {duration_seconds:.1f}s"
        )
        self._logger.info("=" * 60)
        
        summary_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "run_summary",
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "overall_score": overall_score,
            "duration_seconds": round(duration_seconds, 2),
        }
        
        self._write_json_log(summary_entry)
    
    def log_info(self, message: str) -> None:
        """Log an informational message."""
        if self.enabled and self._logger:
            self._logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        if self.enabled and self._logger:
            self._logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        if self.enabled and self._logger:
            self._logger.error(message)
    
    def _write_json_log(self, entry: Dict[str, Any]) -> None:
        """Write a JSON log entry to the NDJSON log file."""
        if self._json_log_path:
            try:
                with open(self._json_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to write JSON log: {e}")
    
    @property
    def json_log_path(self) -> Optional[str]:
        """Get the path to the JSON log file."""
        return self._json_log_path
