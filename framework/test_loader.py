"""
Test Case Loader Module
=======================
Loads and validates test cases from JSON files in the test_cases/ directory.

Test Case Schema:
    {
        "id": "normal_001",
        "input": "What is the capital of France?",
        "expected_behavior": "Should correctly identify Paris as the capital",
        "category": "normal",
        "tags": ["factual", "reasoning"],
        "expected_keywords": ["Paris"],
        "should_refuse": false
    }
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """Represents a single test case for agent evaluation."""
    
    id: str
    input: str
    expected_behavior: str
    category: str
    tags: List[str] = field(default_factory=list)
    expected_keywords: List[str] = field(default_factory=list)
    forbidden_keywords: List[str] = field(default_factory=list)
    should_refuse: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return {
            "id": self.id,
            "input": self.input,
            "expected_behavior": self.expected_behavior,
            "category": self.category,
            "tags": self.tags,
            "expected_keywords": self.expected_keywords,
            "forbidden_keywords": self.forbidden_keywords,
            "should_refuse": self.should_refuse,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """Create a TestCase from a dictionary."""
        return cls(
            id=data["id"],
            input=data["input"],
            expected_behavior=data["expected_behavior"],
            category=data["category"],
            tags=data.get("tags", []),
            expected_keywords=data.get("expected_keywords", []),
            forbidden_keywords=data.get("forbidden_keywords", []),
            should_refuse=data.get("should_refuse", False),
        )


class TestLoader:
    """
    Loads test cases from JSON files in the test cases directory.
    
    Supports:
        - Loading all test cases from a directory
        - Filtering by category
        - Filtering by tags
        - Schema validation
    """
    
    REQUIRED_FIELDS = {"id", "input", "expected_behavior", "category"}
    VALID_CATEGORIES = {"normal", "edge_cases", "adversarial", "safety"}
    
    def __init__(self, test_cases_dir: str = "test_cases"):
        """
        Args:
            test_cases_dir: Path to directory containing test case JSON files.
        """
        self.test_cases_dir = test_cases_dir
        self._test_cases: List[TestCase] = []
    
    def load_all(self) -> List[TestCase]:
        """
        Load all test cases from all JSON files in the test cases directory.
        
        Returns:
            List of all loaded TestCase objects.
            
        Raises:
            FileNotFoundError: If the test cases directory doesn't exist.
        """
        if not os.path.exists(self.test_cases_dir):
            raise FileNotFoundError(
                f"Test cases directory not found: {self.test_cases_dir}"
            )
        
        self._test_cases = []
        
        for filename in sorted(os.listdir(self.test_cases_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(self.test_cases_dir, filename)
                self._test_cases.extend(self._load_file(filepath))
        
        if not self._test_cases:
            raise ValueError(
                f"No test cases found in {self.test_cases_dir}. "
                "Ensure JSON files with valid test cases exist."
            )
        
        return self._test_cases
    
    def load_by_category(self, categories: List[str]) -> List[TestCase]:
        """
        Load test cases filtered by category.
        
        Args:
            categories: List of category names to include.
            
        Returns:
            Filtered list of TestCase objects.
        """
        if not self._test_cases:
            self.load_all()
        
        return [tc for tc in self._test_cases if tc.category in categories]
    
    def load_by_tags(self, tags: List[str]) -> List[TestCase]:
        """
        Load test cases that have any of the specified tags.
        
        Args:
            tags: List of tags to filter by.
            
        Returns:
            Filtered list of TestCase objects.
        """
        if not self._test_cases:
            self.load_all()
        
        return [
            tc for tc in self._test_cases 
            if any(tag in tc.tags for tag in tags)
        ]
    
    def _load_file(self, filepath: str) -> List[TestCase]:
        """Load test cases from a single JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")
        
        if not isinstance(data, list):
            raise ValueError(
                f"Expected a JSON array in {filepath}, got {type(data).__name__}"
            )
        
        test_cases = []
        for i, item in enumerate(data):
            self._validate_test_case(item, filepath, i)
            test_cases.append(TestCase.from_dict(item))
        
        return test_cases
    
    def _validate_test_case(
        self, data: Dict[str, Any], filepath: str, index: int
    ) -> None:
        """Validate a test case has all required fields."""
        missing = self.REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ValueError(
                f"Test case #{index} in {filepath} is missing required fields: "
                f"{missing}"
            )
        
        if data["category"] not in self.VALID_CATEGORIES:
            raise ValueError(
                f"Test case '{data['id']}' in {filepath} has invalid category: "
                f"'{data['category']}'. Valid categories: {self.VALID_CATEGORIES}"
            )
    
    def get_summary(self) -> Dict[str, int]:
        """Get a summary of loaded test cases by category."""
        if not self._test_cases:
            self.load_all()
        
        summary = {}
        for tc in self._test_cases:
            summary[tc.category] = summary.get(tc.category, 0) + 1
        return summary
