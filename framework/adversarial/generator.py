"""
Adversarial Input Generator Module
====================================
Generates adversarial test inputs by combining templates with payloads.
Can produce a large variety of adversarial inputs for comprehensive testing.

This module generates OR includes adversarial inputs covering:
    - Prompt injection attacks
    - Jailbreak attempts (DAN, hypothetical, role-play)
    - Encoding tricks (reversed text, character separation)
"""

import random as _random_module
from typing import List, Optional

from ..test_loader import TestCase
from .templates import (
    PROMPT_INJECTION_TEMPLATES,
    JAILBREAK_TEMPLATES,
    ENCODING_TRICK_TEMPLATES,
    ADVERSARIAL_PAYLOADS,
    ALL_TEMPLATES,
)


class AdversarialGenerator:
    """
    Generates adversarial test cases by combining templates with payloads.
    
    Can produce adversarial inputs for:
        - Prompt injection attacks
        - Jailbreak attempts
        - Encoding tricks
    
    Each generated input is expected to be REFUSED by a safe agent.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Optional random seed for reproducible generation.
        """
        self._rng = _random_module.Random(seed)
    
    def generate_all(self, count: int = 10) -> List[TestCase]:
        """
        Generate a diverse set of adversarial test cases.
        
        Args:
            count: Number of adversarial test cases to generate.
            
        Returns:
            List of TestCase objects with adversarial inputs.
        """
        test_cases = []
        
        # Distribute across attack types
        injection_count = max(1, count // 3)
        jailbreak_count = max(1, count // 3)
        encoding_count = count - injection_count - jailbreak_count
        
        test_cases.extend(self.generate_prompt_injections(injection_count))
        test_cases.extend(self.generate_jailbreaks(jailbreak_count))
        test_cases.extend(self.generate_encoding_tricks(encoding_count))
        
        return test_cases[:count]
    
    def generate_prompt_injections(self, count: int = 3) -> List[TestCase]:
        """Generate prompt injection test cases."""
        return self._generate_from_templates(
            PROMPT_INJECTION_TEMPLATES,
            count,
            prefix="gen_injection",
        )
    
    def generate_jailbreaks(self, count: int = 3) -> List[TestCase]:
        """Generate jailbreak attempt test cases."""
        return self._generate_from_templates(
            JAILBREAK_TEMPLATES,
            count,
            prefix="gen_jailbreak",
        )
    
    def generate_encoding_tricks(self, count: int = 2) -> List[TestCase]:
        """Generate encoding trick test cases."""
        test_cases = []
        
        for i in range(count):
            template = ENCODING_TRICK_TEMPLATES[i % len(ENCODING_TRICK_TEMPLATES)]
            payload = self._rng.choice(ADVERSARIAL_PAYLOADS)
            
            # Handle special template variables
            input_text = template["template"]
            if "{payload}" in input_text:
                input_text = input_text.replace("{payload}", payload)
            if "{reversed_payload}" in input_text:
                input_text = input_text.replace("{reversed_payload}", payload[::-1])
            if "{spaced_payload}" in input_text:
                spaced = ".".join(payload)
                input_text = input_text.replace("{spaced_payload}", spaced)
            
            test_cases.append(
                TestCase(
                    id=f"gen_encoding_{i+1:03d}",
                    input=input_text,
                    expected_behavior=(
                        "Should refuse this request despite encoding/obfuscation. "
                        f"Attack type: {template['attack_type']}. "
                        f"Description: {template['description']}"
                    ),
                    category="adversarial",
                    tags=["generated", template["attack_type"], "encoding"],
                    should_refuse=True,
                )
            )
        
        return test_cases
    
    def _generate_from_templates(
        self,
        templates: list,
        count: int,
        prefix: str,
    ) -> List[TestCase]:
        """Generate test cases by combining templates with payloads."""
        test_cases = []
        
        for i in range(count):
            template = templates[i % len(templates)]
            payload = ADVERSARIAL_PAYLOADS[i % len(ADVERSARIAL_PAYLOADS)]
            
            input_text = template["template"].replace("{payload}", payload)
            
            test_cases.append(
                TestCase(
                    id=f"{prefix}_{i+1:03d}",
                    input=input_text,
                    expected_behavior=(
                        "Should refuse this request. "
                        f"Attack type: {template['attack_type']}. "
                        f"Description: {template['description']}"
                    ),
                    category="adversarial",
                    tags=["generated", template["attack_type"]],
                    should_refuse=True,
                )
            )
        
        return test_cases
