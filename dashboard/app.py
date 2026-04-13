"""
Agent Testing Framework — Streamlit Dashboard
===============================================
Interactive dashboard for visualizing test results.

Run with:
    pip install streamlit
    streamlit run dashboard/app.py

The dashboard loads results from the latest test run
(results/results.json) and displays interactive charts
and detailed analysis.
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed. Install with: pip install streamlit")
    print("Then run: streamlit run dashboard/app.py")
    sys.exit(1)


# ==============================================================================
# Page Configuration
# ==============================================================================

st.set_page_config(
    page_title="Agent Testing Framework — Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark premium styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(120deg, #3b82f6, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .score-box {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .score-value {
        font-size: 2.5rem;
        font-weight: 700;
    }
    .score-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .pass-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .pass-badge-pass {
        background: rgba(74, 222, 128, 0.2);
        color: #4ade80;
    }
    .pass-badge-fail {
        background: rgba(248, 113, 113, 0.2);
        color: #f87171;
    }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# Data Loading
# ==============================================================================

def load_results(filepath: str = None) -> dict:
    """Load test results from JSON file."""
    if filepath is None:
        # Look for results in common locations
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "results.json"),
            "results/results.json",
            "../results/results.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                filepath = path
                break
    
    if filepath is None or not os.path.exists(filepath):
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# Dashboard Layout
# ==============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🔬 Agent Testing Framework</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive Dashboard for Test Results Analysis</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # File uploader in sidebar
    uploaded_file = st.sidebar.file_uploader(
        "Upload results.json",
        type=["json"],
        help="Upload a results.json file from a test run"
    )
    
    # Load data
    if uploaded_file:
        data = json.load(uploaded_file)
    else:
        data = load_results()
    
    if data is None:
        st.warning(
            "⚠️ No results found. Run the test framework first:\n\n"
            "```bash\n"
            "python run_tests.py --agent rule_based --no-llm-judge\n"
            "```\n\n"
            "Or upload a `results.json` file using the sidebar."
        )
        return
    
    # Extract data
    metadata = data.get("metadata", {})
    summary = data.get("summary", {})
    results = data.get("results", [])
    
    agent_name = metadata.get("agent_name", "Unknown")
    timestamp = metadata.get("timestamp", "N/A")
    
    st.sidebar.markdown(f"**Agent:** {agent_name}")
    st.sidebar.markdown(f"**Run Time:** {timestamp[:19]}")
    st.sidebar.markdown(f"**Total Tests:** {summary.get('total_tests', 0)}")
    
    # Category filter
    categories = list(set(r.get("category", "unknown") for r in results))
    selected_categories = st.sidebar.multiselect(
        "Filter by Category",
        options=categories,
        default=categories,
    )
    
    # Filter results
    filtered_results = [r for r in results if r.get("category") in selected_categories]
    
    # =========================================================================
    # Row 1: Score Cards
    # =========================================================================
    st.markdown("### 📊 Aggregate Scores")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Overall Score",
            value=f"{summary.get('overall_score', 0)}/10",
        )
    with col2:
        st.metric(
            label="🛡️ Safety",
            value=f"{summary.get('safety_score', 0)}/10",
        )
    with col3:
        st.metric(
            label="🎯 Accuracy",
            value=f"{summary.get('accuracy_score', 0)}/10",
        )
    with col4:
        st.metric(
            label="💪 Robustness",
            value=f"{summary.get('robustness_score', 0)}/10",
        )
    with col5:
        pass_rate = summary.get("pass_rate", 0)
        st.metric(
            label="✅ Pass Rate",
            value=f"{pass_rate}%",
        )
    
    st.divider()
    
    # =========================================================================
    # Row 2: Charts
    # =========================================================================
    st.markdown("### 📈 Visual Analysis")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Category pass rates bar chart
        category_pass_rates = summary.get("category_pass_rates", {})
        if category_pass_rates:
            import pandas as pd
            df_pass = pd.DataFrame({
                "Category": [k.replace("_", " ").title() for k in category_pass_rates.keys()],
                "Pass Rate (%)": list(category_pass_rates.values()),
            })
            st.bar_chart(df_pass.set_index("Category"), height=350)
            st.caption("Pass Rate by Category (%)")
    
    with chart_col2:
        # Category scores
        category_scores = summary.get("category_scores", {})
        if category_scores:
            import pandas as pd
            cats = list(category_scores.keys())
            df_scores = pd.DataFrame({
                "Category": [c.replace("_", " ").title() for c in cats],
                "Correctness": [category_scores[c].get("correctness", 0) for c in cats],
                "Relevance": [category_scores[c].get("relevance", 0) for c in cats],
                "Safety": [category_scores[c].get("safety", 0) for c in cats],
            })
            st.bar_chart(df_scores.set_index("Category"), height=350)
            st.caption("Scores by Category (0-10)")
    
    st.divider()
    
    # =========================================================================
    # Row 3: Pass/Fail Distribution
    # =========================================================================
    
    dist_col1, dist_col2 = st.columns(2)
    
    with dist_col1:
        st.markdown("### 📋 Test Distribution")
        passed = summary.get("passed_tests", 0)
        failed = summary.get("failed_tests", 0)
        
        import pandas as pd
        df_dist = pd.DataFrame({
            "Status": ["Passed", "Failed"],
            "Count": [passed, failed],
        })
        st.bar_chart(df_dist.set_index("Status"), height=250)
    
    with dist_col2:
        st.markdown("### ⏱️ Timing Statistics")
        timing = summary.get("timing_stats", {})
        if timing:
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.metric("Mean", f"{timing.get('mean_ms', 0):.1f} ms")
                st.metric("Min", f"{timing.get('min_ms', 0):.1f} ms")
            with t_col2:
                st.metric("Median", f"{timing.get('median_ms', 0):.1f} ms")
                st.metric("Max", f"{timing.get('max_ms', 0):.1f} ms")
            st.metric("P95", f"{timing.get('p95_ms', 0):.1f} ms")
    
    st.divider()
    
    # =========================================================================
    # Row 4: Detailed Results Table
    # =========================================================================
    st.markdown("### 🧪 Detailed Test Results")
    
    if filtered_results:
        import pandas as pd
        
        table_data = []
        for r in filtered_results:
            scores = r.get("evaluation_scores", {})
            table_data.append({
                "Test ID": r.get("test_id", ""),
                "Category": r.get("category", ""),
                "Status": "✅ PASS" if r.get("passed", False) else "❌ FAIL",
                "Correctness": scores.get("correctness", -1),
                "Safety": scores.get("safety", -1),
                "Latency (ms)": f"{r.get('latency_ms', 0):.1f}",
                "Details": r.get("details", "")[:100],
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            column_config={
                "Correctness": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=10,
                    format="%.1f",
                ),
                "Safety": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=10,
                    format="%.1f",
                ),
            }
        )
    else:
        st.info("No results match the selected categories.")
    
    st.divider()
    
    # =========================================================================
    # Row 5: Failure Analysis
    # =========================================================================
    failures = summary.get("failures", [])
    
    st.markdown("### ❌ Failure Analysis")
    
    if failures:
        filtered_failures = [f for f in failures if f.get("category") in selected_categories]
        
        if filtered_failures:
            for i, f in enumerate(filtered_failures):
                with st.expander(
                    f"🔴 {f.get('test_id', 'Unknown')} — {f.get('category', '')}",
                    expanded=(i == 0),
                ):
                    st.markdown(f"**Input:** `{f.get('input', '')}`")
                    st.markdown(f"**Output:** `{f.get('output', '')}`")
                    st.markdown(f"**Details:** {f.get('details', '')}")
                    st.markdown(f"**Scores:** {f.get('scores', '')}")
        else:
            st.success("🎉 No failures in selected categories!")
    else:
        st.success("🎉 All tests passed! No failures to report.")
    
    st.divider()
    
    # =========================================================================
    # Row 6: Individual Test Details (expandable)
    # =========================================================================
    st.markdown("### 🔍 Test Case Inspector")
    
    if filtered_results:
        test_ids = [r.get("test_id", f"test_{i}") for i, r in enumerate(filtered_results)]
        selected_test = st.selectbox("Select a test case", test_ids)
        
        if selected_test:
            test_data = next(
                (r for r in filtered_results if r.get("test_id") == selected_test),
                None,
            )
            
            if test_data:
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**Input:**")
                    st.code(test_data.get("test_input", ""), language=None)
                    
                    st.markdown("**Expected Behavior:**")
                    st.info(test_data.get("expected_behavior", ""))
                
                with detail_col2:
                    st.markdown("**Agent Output:**")
                    st.code(test_data.get("agent_output", ""), language=None)
                    
                    st.markdown("**Evaluation Details:**")
                    if test_data.get("passed"):
                        st.success(test_data.get("details", ""))
                    else:
                        st.error(test_data.get("details", ""))
                
                # Show rule-based checks
                checks = test_data.get("rule_based_checks", [])
                if checks:
                    st.markdown("**Rule-Based Checks:**")
                    import pandas as pd
                    checks_df = pd.DataFrame([
                        {
                            "Check": c.get("name", ""),
                            "Status": "✅ Pass" if c.get("passed") else "❌ Fail",
                            "Reason": c.get("reason", ""),
                        }
                        for c in checks
                    ])
                    st.dataframe(checks_df, use_container_width=True)
    
    # Footer
    st.divider()
    st.markdown(
        '<div style="text-align: center; color: #64748b; padding: 1rem;">'
        'Agent Testing Framework v1.0.0 — Dashboard'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
