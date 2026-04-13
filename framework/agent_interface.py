"""
Agent Interface Module
======================
Defines the agent-agnostic interface that any AI agent must satisfy
to be tested by this framework.

Any agent can be plugged in as long as it implements:
    def run_agent(input: str) -> str

This ensures:
    - Reusability across different agent implementations
    - Standardization of the testing interface
    - Easy integration with any LLM framework (LangChain, LlamaIndex, OpenAI SDK, etc.)
"""

from typing import Protocol, Callable, runtime_checkable


@runtime_checkable
class AgentInterface(Protocol):
    """
    Protocol defining the interface that any agent must implement.
    
    Any class that has a `run_agent(input: str) -> str` method
    automatically satisfies this protocol (structural subtyping).
    
    Example:
        class MyAgent:
            def run_agent(self, input: str) -> str:
                return "Hello, " + input
        
        # MyAgent automatically satisfies AgentInterface
        agent = MyAgent()
        assert isinstance(agent, AgentInterface)
    """
    
    def run_agent(self, input: str) -> str:
        """
        Process an input string and return a response string.
        
        Args:
            input: The user query or prompt to send to the agent.
            
        Returns:
            The agent's response as a string.
        """
        ...


class FunctionAgent:
    """
    Wrapper that adapts a simple function into an AgentInterface.
    
    This allows users to plug in a plain function without
    creating a class:
    
    Example:
        def my_agent(input: str) -> str:
            return "Response to: " + input
        
        agent = FunctionAgent(my_agent)
        result = agent.run_agent("Hello")
    """
    
    def __init__(self, fn: Callable[[str], str], name: str = "FunctionAgent"):
        """
        Args:
            fn: A callable that takes a string input and returns a string output.
            name: Optional name for this agent (used in reports).
        """
        if not callable(fn):
            raise TypeError(f"Expected a callable, got {type(fn).__name__}")
        self._fn = fn
        self.name = name
    
    def run_agent(self, input: str) -> str:
        """Execute the wrapped function."""
        return self._fn(input)
    
    def __repr__(self) -> str:
        return f"FunctionAgent(name='{self.name}')"


def wrap_agent(fn: Callable[[str], str], name: str = "WrappedAgent") -> FunctionAgent:
    """
    Convenience function to wrap a simple function into an AgentInterface.
    
    Args:
        fn: A function with signature (str) -> str
        name: Optional name for the agent
        
    Returns:
        A FunctionAgent instance that satisfies AgentInterface
        
    Example:
        def my_bot(input: str) -> str:
            return f"Echo: {input}"
        
        agent = wrap_agent(my_bot, name="EchoBot")
        result = agent.run_agent("test")
    """
    return FunctionAgent(fn, name=name)


def validate_agent(agent) -> bool:
    """
    Validate that an object satisfies the AgentInterface protocol.
    
    Args:
        agent: The object to validate.
        
    Returns:
        True if the agent has a valid run_agent method.
        
    Raises:
        TypeError: If the agent doesn't satisfy the interface.
    """
    if not isinstance(agent, AgentInterface):
        raise TypeError(
            f"Agent of type '{type(agent).__name__}' does not satisfy AgentInterface. "
            f"It must have a 'run_agent(self, input: str) -> str' method."
        )
    return True
