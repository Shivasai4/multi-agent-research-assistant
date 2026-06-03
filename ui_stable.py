import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from src.graph.workflow import research_app  # Use your working graph
from src.graph.state import GraphState
from src.config import settings

st.set_page_config(page_title="Multi-Agent Research Assistant", layout="wide")
st.title("🤖 Multi-Agent Research Assistant")
st.markdown("Ask any research question. A team of AI agents will plan, search, analyze, and write a report for you.")

# Session state
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "running" not in st.session_state:
    st.session_state.running = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    max_revisions = st.slider("Max revision attempts", 1, 5, 2)
    if st.button("🗑️ Clear Cache"):
        st.session_state.cache.clear()
        st.success("Cache cleared")
    st.caption("Agents: Planner → Retriever → Researcher → Analyst → Writer")

# Main query
query = st.text_area("📝 Your research question:", height=100,
                     placeholder="Example: What is Ollama and how does it work?")

col1, col2 = st.columns([1, 1])
with col1:
    start = st.button("🔍 Start Research", type="primary", disabled=st.session_state.running, use_container_width=True)

if start and query.strip():
    # Check cache
    if query in st.session_state.cache:
        report, score = st.session_state.cache[query]
        st.success(f"✅ Using cached result (review score: {score}/10)")
        st.markdown("## 📄 Final Report")
        st.markdown(report)
        st.download_button("📥 Download Report", report, f"cached_report_{query[:30]}.md", mime="text/markdown")
        st.stop()
    
    st.session_state.running = True
    start_time = time.time()
    
    # Build initial state
    initial_state: GraphState = {
        "user_query": query,
        "plan": None,
        "current_step": 0,
        "raw_documents": [],
        "search_results": [],
        "vector_results": [],
        "analysis": None,
        "review": None,
        "revision_count": 0,
        "max_revisions": max_revisions,
        "final_report": None,
        "errors": [],
        "agent_traces": []
    }
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0, text="Starting...")
    status_placeholder.info("🤖 Agents are working (this may take 30-90 seconds)...")
    
    # Run the graph (blocking, but we show a simple progress)
    try:
        final_state = research_app.invoke(initial_state)
    except Exception as e:
        st.error(f"Research failed: {e}")
        st.session_state.running = False
        st.stop()
    
    elapsed = time.time() - start_time
    progress_bar.progress(1.0, text="Completed!")
    
    report = final_state.get("final_report", "No report generated.")
    review_score = final_state.get("review", {}).get("score") if final_state.get("review") else None
    st.session_state.cache[query] = (report, review_score)
    
    status_placeholder.success(f"✅ Research completed in {elapsed:.1f} seconds. Review score: {review_score}/10")
    
    # Display report
    st.markdown("## 📄 Final Report")
    st.markdown(report)
    st.download_button(
        label="📥 Download Report (Markdown)",
        data=report,
        file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )
    
    st.session_state.running = False