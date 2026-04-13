# Agent Testing Framework 🔬

A comprehensive, **agent-agnostic** framework for testing any AI agent using predefined test cases, automated evaluation, adversarial testing, and detailed reporting.

## 🎯 Overview

Most AI systems fail not because of poor models — but due to:
- ❌ Lack of testing
- ❌ No guardrail validation
- ❌ No evaluation pipeline

This framework fixes that by providing a complete testing pipeline that works with **any AI agent**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Agent-Agnostic** | Test any agent via a simple `run_agent(input: str) -> str` interface |
| **20 Test Cases** | Pre-built tests across 4 categories: Normal, Edge Cases, Adversarial, Safety |
| **Dual Evaluation** | LLM-as-a-Judge (OpenAI) + Rule-based checks (no API needed) |
| **Adversarial Testing** | Prompt injection, jailbreak attempts, encoding tricks |
| **Metrics & Scoring** | Safety (40%), Accuracy (35%), Robustness (25%) aggregate scores |
| **Rich Reports** | Terminal (Rich), HTML (Chart.js), JSON output |
| **Observability** | Structured JSON logs for every test execution |
| **Timing Stats** | Mean, Median, Min, Max, P95 latency tracking |
| **3 Sample Agents** | Echo, Rule-based, OpenAI Chatbot — plug and play |
| **Dashboard** | Optional Streamlit dashboard for visual analysis |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Tests (No API Key Needed!)

```bash
# Test with the rule-based agent (no API key required)
python run_tests.py --agent rule_based --no-llm-judge

# Test with the echo agent
python run_tests.py --agent echo --no-llm-judge
```

### 3. View Reports

After running, find your reports in the `results/` directory:
- `results/report.html` — Interactive HTML report with charts
- `results/results.json` — Machine-readable JSON results
- `results/logs/` — Structured JSON logs for observability

## 📖 Detailed Usage

### Command Line Options

```bash
python run_tests.py [OPTIONS]

Options:
  --agent {echo,rule_based,simple_chatbot}
                        Agent to test (default: rule_based)
  --categories CATEGORIES
                        Comma-separated categories: normal,edge_cases,adversarial,safety
  --no-llm-judge        Disable LLM-as-a-Judge (rule-based evaluation only)
  --no-generated-adversarial
                        Skip dynamically generated adversarial tests
  --output OUTPUT       Output directory for reports (default: results/)
  --config CONFIG       Path to config file (default: config.yaml)
  --report-formats FORMATS
                        Comma-separated: terminal,html,json
```

### Examples

```bash
# Run all tests with terminal + HTML reports
python run_tests.py --agent rule_based --no-llm-judge

# Run only adversarial and safety tests
python run_tests.py --agent rule_based --categories adversarial,safety --no-llm-judge

# Run with JSON output only
python run_tests.py --agent rule_based --report-formats json --no-llm-judge

# Run with a custom config
python run_tests.py --agent rule_based --config my_config.yaml --no-llm-judge
```

## 🔑 OpenAI API Key (Optional)

The LLM-as-a-Judge evaluation component uses OpenAI's GPT to score agent responses on Correctness, Relevance, and Safety. This provides a more nuanced evaluation layer.

### Current Configuration: DUMMY Key

The default `config.yaml` ships with a **DUMMY API key** for demonstration purposes:

```yaml
openai:
  api_key: "sk-dummy-key-replace-with-your-actual-openai-api-key"
```

**This dummy key will NOT make real API calls.** The framework detects it and gracefully falls back to rule-based evaluation only.

### To Enable LLM-as-a-Judge

1. **Option A: Environment Variable** (Recommended)
   ```bash
   export OPENAI_API_KEY="sk-your-real-api-key-here"
   python run_tests.py --agent rule_based
   ```

2. **Option B: Update config.yaml**
   ```yaml
   openai:
     api_key: "sk-your-real-api-key-here"
   ```

### Without an API Key

The framework is **fully functional without any API key**:
- Rule-based evaluation covers: refusal detection, keyword matching, PII detection, response quality
- Use `--no-llm-judge` flag to explicitly disable LLM evaluation
- All sample agents work without API keys (SimpleChatbot returns placeholder responses)

## 🧩 Plugging In Your Own Agent

### Method 1: Simple Function

```python
from framework.agent_interface import wrap_agent
from framework.runner import TestRunner

def my_agent(input: str) -> str:
    # Your agent logic here
    return "Response to: " + input

agent = wrap_agent(my_agent, name="MyAgent")
runner = TestRunner()
results, report = runner.run(agent)
```

### Method 2: Class-based Agent

```python
from framework.runner import TestRunner

class MyLLMAgent:
    name = "MyLLMAgent"
    
    def run_agent(self, input: str) -> str:
        # Your agent logic (LangChain, LlamaIndex, etc.)
        return "response"

runner = TestRunner()
results, report = runner.run(MyLLMAgent())
```

## 📊 Scoring System

### Dimensions
| Dimension | Weight | Threshold | Description |
|-----------|--------|-----------|-------------|
| Safety | 40% | ≥ 8/10 | Safe, ethical, appropriate responses |
| Accuracy | 35% | ≥ 7/10 | Factually correct and complete |
| Robustness | 25% | Pass rate | Performance on adversarial/edge cases |

### Pass/Fail Criteria
- **Correctness** score ≥ 7/10 → Pass
- **Safety** score ≥ 8/10 → Pass (stricter threshold)
- Must refuse harmful requests (detected via rule-based checks)

## 📁 Project Structure

```
agent-testing-framework/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config.yaml                  # Framework configuration
├── run_tests.py                 # CLI entry point
│
├── framework/                   # Core framework
│   ├── agent_interface.py       # Agent-agnostic interface
│   ├── test_loader.py           # Test case loading & validation
│   ├── runner.py                # Main test runner/orchestrator
│   ├── evaluators/
│   │   ├── base.py              # Base evaluator interface
│   │   ├── rule_based.py        # Rule-based checks
│   │   └── llm_judge.py         # LLM-as-a-Judge evaluator
│   ├── adversarial/
│   │   ├── templates.py         # Attack templates
│   │   └── generator.py         # Adversarial input generator
│   ├── metrics/
│   │   └── scoring.py           # Scoring engine
│   ├── reporting/
│   │   ├── terminal_report.py   # Rich terminal output
│   │   └── html_report.py       # HTML report generation
│   └── observability/
│       └── logger.py            # Structured JSON logging
│
├── test_cases/                  # Test case definitions
│   ├── normal.json              # 5 normal test cases
│   ├── edge_cases.json          # 5 edge case test cases
│   ├── adversarial.json         # 5 adversarial test cases
│   └── safety.json              # 5 safety test cases
│
├── sample_agents/               # Sample agent implementations
│   ├── echo_agent.py            # Echo agent (smoke testing)
│   ├── rule_based_agent.py      # Deterministic agent (no API key)
│   └── simple_chatbot.py        # OpenAI chatbot (needs API key)
│
├── dashboard/                   # Streamlit dashboard (optional)
│   └── app.py
│
├── results/                     # Generated reports (after running)
│   ├── report.html
│   ├── results.json
│   └── logs/
│
└── tests/                       # Unit tests
    └── test_framework.py
```

## 🧪 Running Unit Tests

```bash
python -m pytest tests/ -v
```

## 📈 Dashboard (Optional)

Launch the Streamlit dashboard to visualize results:

```bash
pip install streamlit
streamlit run dashboard/app.py
```

## 🔧 Configuration

All settings are in `config.yaml`:

| Section | Key Settings |
|---------|-------------|
| `openai` | API key, model, temperature |
| `testing` | Test cases directory, timeout, categories |
| `evaluation` | LLM judge toggle, scoring thresholds, weights |
| `reporting` | Output directory, report formats |
| `observability` | Logging toggle, log level, log directory |

## 📋 Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| Normal | 5 | Basic factual queries, coding, translation |
| Edge Cases | 5 | Empty input, gibberish, multi-language, extreme math |
| Adversarial | 5+5 | Prompt injection, jailbreaks + generated attacks |
| Safety | 5 | Harmful requests, PII, hate speech, misinformation |

## 📝 License

MIT License — Feel free to use and modify.
