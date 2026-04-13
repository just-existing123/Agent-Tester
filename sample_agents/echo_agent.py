"""
Echo Agent
==========
A trivial agent that echoes back the input.

This agent is useful for smoke-testing the framework itself.
It always returns the input as-is, making it predictable for
verifying that test execution, evaluation, and reporting work correctly.

This agent is NOT expected to pass safety or adversarial tests,
since it will echo back harmful content without refusing.
"""


class EchoAgent:
    """
    Simple echo agent — returns the input as-is.
    
    Usage:
        agent = EchoAgent()
        response = agent.run_agent("Hello!")  # Returns "Echo: Hello!"
    """
    
    name = "EchoAgent"
    
    def run_agent(self, input: str) -> str:
        """Echo back the input with a prefix."""
        if not input or not input.strip():
            return "Echo: [empty input received]"
        return f"Echo: {input}"
