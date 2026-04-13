"""
Rule-Based Agent
================
A deterministic agent with hardcoded responses for common queries.

This agent is useful for testing the framework WITHOUT any API keys.
It provides predictable, known responses that make it easy to verify
that evaluation and scoring work correctly.

The agent has built-in safety guardrails — it refuses harmful requests
and responds appropriately to different query types.
"""

import re
from typing import Dict, List, Optional


class RuleBasedAgent:
    """
    A deterministic agent that uses pattern matching to respond.
    
    Has built-in safety guardrails for refusing harmful requests,
    and provides reasonable responses for common query types.
    
    Usage:
        agent = RuleBasedAgent()
        response = agent.run_agent("What is the capital of France?")
    """
    
    name = "RuleBasedAgent"
    
    # Safety patterns — if input matches these, the agent refuses
    SAFETY_REFUSE_PATTERNS = [
        r"(how to |make |build |create ).*(bomb|explosive|weapon)",
        r"(hack|breach|break into|unauthorized access)",
        r"(phishing|steal|credentials|password.*steal)",
        r"(racial slur|hate speech|discriminat)",
        r"(drug|methamphetamine|cocaine|heroin).*(synthe|make|cook|produce|create)",
        r"(fake news|misinformation|disinformation)",
        r"(social security|SSN|credit card).*(remember|store|repeat)",
        r"(stalk|harass|spy on)",
        r"(DDoS|denial.of.service|malware|ransomware|virus.*create)",
        r"(pick a lock|break.*into.*house|burglar)",
    ]
    
    # Adversarial patterns — detect jailbreak / prompt injection attempts
    ADVERSARIAL_PATTERNS = [
        r"ignore (all |previous )?instructions",
        r"you are now (DAN|an AI without)",
        r"(debug mode|maintenance mode|admin mode)",
        r"(print|reveal|show) (your |the )?(system prompt|instructions|hidden)",
        r"no (restrictions|filters|safety|rules|guidelines)",
        r"(do anything now|no restrictions|no boundaries)",
        r"(pretend|act as|role.?play).*(no safety|without filter|unrestricted)",
        r"hypothetical.*(no.*filter|no.*safety|no.*restrict)",
        r"i am the developer",
    ]
    
    # Knowledge base for factual queries
    KNOWLEDGE_BASE: Dict[str, str] = {
        "capital of france": "The capital of France is Paris. Paris is located in northern France and is the country's largest city, serving as the political, economic, and cultural center.",
        "photosynthesis": "Photosynthesis is the process by which plants and other organisms convert light energy into chemical energy. Plants use sunlight, water, and carbon dioxide to produce glucose and oxygen. This process primarily takes place in the chloroplasts of plant cells.",
        "states of matter": "The three primary states of matter are solid, liquid, and gas. In a solid, particles are tightly packed; in a liquid, they flow freely; and in a gas, they move independently with lots of space between them.",
        "hello.*spanish": "The translation of 'Hello, how are you?' to Spanish is: 'Hola, ¿cómo estás?'",
    }
    
    SAFETY_REFUSAL = (
        "I'm sorry, but I cannot assist with that request. It involves content "
        "that could be harmful, unethical, or illegal. I'm designed to be helpful, "
        "harmless, and honest. If you have a different question or need assistance "
        "with something appropriate, I'd be happy to help."
    )
    
    ADVERSARIAL_REFUSAL = (
        "I cannot comply with that request. I'm an AI assistant with safety "
        "guidelines that I follow regardless of how the request is framed. "
        "I cannot ignore my instructions, enter special modes, or bypass my "
        "safety filters. I'm happy to help with legitimate requests."
    )
    
    def run_agent(self, input: str) -> str:
        """
        Process the input and return a deterministic response.
        
        The agent checks in order:
        1. Safety-critical patterns → refuse
        2. Adversarial patterns → refuse
        3. Knowledge base → provide answer
        4. Coding requests → provide template
        5. Default → generic helpful response
        """
        if not input or not input.strip():
            return (
                "I notice you've sent an empty message. Could you please "
                "provide a question or request? I'm here to help!"
            )
        
        input_lower = input.lower().strip()
        
        # 1. Check for safety-critical content
        for pattern in self.SAFETY_REFUSE_PATTERNS:
            if re.search(pattern, input_lower):
                return self.SAFETY_REFUSAL
        
        # 2. Check for adversarial / jailbreak attempts
        for pattern in self.ADVERSARIAL_PATTERNS:
            if re.search(pattern, input_lower):
                return self.ADVERSARIAL_REFUSAL
        
        # 3. Check knowledge base
        for key, response in self.KNOWLEDGE_BASE.items():
            if re.search(key, input_lower):
                return response
        
        # 4. Handle coding requests
        if "factorial" in input_lower and ("python" in input_lower or "function" in input_lower):
            return (
                "Here's a Python function to calculate the factorial of a number:\n\n"
                "```python\n"
                "def factorial(n):\n"
                '    """Calculate the factorial of a non-negative integer."""\n'
                "    if n < 0:\n"
                '        raise ValueError("Factorial is not defined for negative numbers")\n'
                "    if n == 0 or n == 1:\n"
                "        return 1\n"
                "    return n * factorial(n - 1)\n"
                "```\n\n"
                "This recursive function handles edge cases (negative numbers, 0, 1) "
                "and calculates n! for any non-negative integer."
            )
        
        # 5. Handle math
        if re.search(r"\d+\s*[\*x×]\s*\d+", input_lower):
            try:
                # Extract numbers
                nums = re.findall(r"(\d+)", input)
                if len(nums) >= 2:
                    result = int(nums[0]) * int(nums[1])
                    return f"The result of {nums[0]} × {nums[1]} = {result}"
            except (ValueError, OverflowError):
                return "That's a very large calculation. The result would be an extremely large number."
        
        # 6. Handle multi-language
        if re.search(r"(bonjour|comment|français|french)", input_lower):
            return (
                "Bonjour! Je vois que vous écrivez en français. "
                "I can communicate in multiple languages. "
                "Comment puis-je vous aider aujourd'hui?"
            )
        
        # 7. Handle gibberish / nonsensical input
        words = input.split()
        if len(words) > 3:
            real_words = sum(1 for w in words if len(w) > 1 and w.isalpha())
            if real_words / len(words) < 0.3:
                return (
                    "I'm sorry, I couldn't understand your input. It appears to contain "
                    "random characters or nonsensical text. Could you please rephrase "
                    "your question clearly so I can assist you?"
                )
        
        # 8. Multi-part queries
        if input.count("?") >= 2:
            return (
                "I see you've asked multiple questions. Let me address each one:\n\n"
                "Regarding your queries — this is a rule-based agent with limited "
                "knowledge. For comprehensive answers to multi-part questions, "
                "I would recommend using a more advanced AI model. However, I can "
                "attempt to address each part of your query to the best of my ability."
            )
        
        # 9. Default response
        return (
            f"Thank you for your question. While I'm a rule-based agent with "
            f"limited knowledge, I understand you're asking about: '{input[:100]}'. "
            f"For the most accurate and detailed response, I would recommend "
            f"consulting a more advanced AI model or reliable sources on this topic."
        )
