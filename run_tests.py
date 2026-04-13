#!/usr/bin/env python3
"""
Agent Testing Framework — CLI Entry Point
==========================================
Main script to run the agent testing framework from the command line.

Usage:
    # Run all tests with the rule-based agent (no API key needed)
    python run_tests.py --agent rule_based

    # Run all tests with the echo agent
    python run_tests.py --agent echo

    # Run all tests with the simple chatbot (needs OpenAI API key)
    python run_tests.py --agent simple_chatbot

    # Run specific categories only
    python run_tests.py --agent rule_based --categories normal,adversarial

    # Run without LLM judge (rule-based evaluation only)
    python run_tests.py --agent rule_based --no-llm-judge

    # Specify output directory
    python run_tests.py --agent rule_based --output results/my_run

    # Skip generated adversarial tests
    python run_tests.py --agent rule_based --no-generated-adversarial

NOTE: The default configuration uses a DUMMY OpenAI API key.
      To enable LLM-as-a-Judge evaluation, set a valid OPENAI_API_KEY
      environment variable or update the api_key in config.yaml.
"""

import argparse
import sys
import os

# Fix encoding for Windows console (allows emoji in output)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.runner import TestRunner


def get_agent(agent_name: str):
    """
    Get an agent instance by name.
    
    Args:
        agent_name: One of 'echo', 'rule_based', 'simple_chatbot'
        
    Returns:
        An agent instance that implements AgentInterface.
    """
    agents = {
        "echo": ("sample_agents.echo_agent", "EchoAgent"),
        "rule_based": ("sample_agents.rule_based_agent", "RuleBasedAgent"),
        "simple_chatbot": ("sample_agents.simple_chatbot", "SimpleChatbot"),
    }
    
    if agent_name not in agents:
        print(f"❌ Unknown agent: '{agent_name}'")
        print(f"   Available agents: {', '.join(agents.keys())}")
        sys.exit(1)
    
    module_path, class_name = agents[agent_name]
    
    try:
        import importlib
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        return agent_class()
    except ImportError as e:
        print(f"❌ Failed to import agent '{agent_name}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🔬 Agent Testing Framework — Test any AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --agent rule_based
  python run_tests.py --agent echo --no-llm-judge
  python run_tests.py --agent rule_based --categories normal,safety
  python run_tests.py --agent simple_chatbot --output results/chatbot_run
        """,
    )
    
    parser.add_argument(
        "--agent",
        type=str,
        default="rule_based",
        choices=["echo", "rule_based", "simple_chatbot"],
        help="Agent to test (default: rule_based)",
    )
    
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of test categories to run (default: all)",
    )
    
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        default=False,
        help="Disable LLM-as-a-Judge evaluation (use rule-based only)",
    )
    
    parser.add_argument(
        "--no-generated-adversarial",
        action="store_true",
        default=False,
        help="Skip dynamically generated adversarial test cases",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for reports (default: results/)",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    
    parser.add_argument(
        "--report-formats",
        type=str,
        default=None,
        help="Comma-separated report formats: terminal,html,json (default: all)",
    )
    
    args = parser.parse_args()
    
    # Parse categories
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]
    
    # Parse report formats
    report_formats = None
    if args.report_formats:
        report_formats = [f.strip() for f in args.report_formats.split(",")]
    
    # Get agent
    print(f"🔬 Agent Testing Framework v1.0.0")
    print(f"{'=' * 50}")
    print(f"Agent:      {args.agent}")
    print(f"LLM Judge:  {'Disabled' if args.no_llm_judge else 'Enabled (if API key valid)'}")
    print(f"Categories: {categories or 'All'}")
    print(f"Config:     {args.config}")
    print(f"{'=' * 50}\n")
    
    agent = get_agent(args.agent)
    
    # Initialize runner
    runner = TestRunner(
        config_path=args.config,
        output_dir=args.output,
    )
    
    # Run tests
    try:
        results, report = runner.run(
            agent=agent,
            categories=categories,
            use_llm_judge=not args.no_llm_judge,
            include_generated_adversarial=not args.no_generated_adversarial,
            report_formats=report_formats,
        )
        
        # Exit code based on results
        if report.pass_rate < 50:
            sys.exit(2)  # More than half the tests failed
        elif report.failed_tests > 0:
            sys.exit(1)  # Some tests failed
        else:
            sys.exit(0)  # All tests passed
            
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
