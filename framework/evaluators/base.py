"""
Base Evaluator Module
=====================
Defines the abstract base class for all evaluators and the
EvaluationResult data class that standardizes evaluation output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class EvaluationResult:
    """
    Standardized result from any evaluator.
    
    Attributes:
        evaluator_name: Name of the evaluator that produced this result.
        scores: Dictionary of score dimensions (e.g., correctness, relevance, safety).
                Each score is a float from 0.0 to 10.0.
        passed: Whether the test case passed according to this evaluator.
        details: Human-readable explanation of the evaluation.
        checks: List of individual check results (for rule-based evaluators).
        raw_response: Raw response from the evaluator (e.g., LLM judge response).
    """
    
    evaluator_name: str
    scores: Dict[str, float] = field(default_factory=dict)
    passed: bool = True
    details: str = ""
    checks: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "evaluator_name": self.evaluator_name,
            "scores": self.scores,
            "passed": self.passed,
            "details": self.details,
            "checks": self.checks,
        }


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.
    
    Subclasses must implement the `evaluate` method.
    """
    
    def __init__(self, name: str = "BaseEvaluator"):
        self.name = name
    
    @abstractmethod
    def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_behavior: str,
        test_case: Any = None,
    ) -> EvaluationResult:
        """
        Evaluate an agent's response.
        
        Args:
            input_text: The original input sent to the agent.
            output_text: The agent's response.
            expected_behavior: Description of what the agent should do.
            test_case: Optional full TestCase object for additional context.
            
        Returns:
            An EvaluationResult with scores and pass/fail determination.
        """
        ...
