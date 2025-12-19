"""
EvoLoop Trace Viewer - Streamlit Application

A visual interface for domain experts to review traces and annotate.

Run with: evoloop ui
Or: streamlit run src/evoloop/ui/app.py
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

import streamlit as st

# Add parent to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(__file__).rsplit("/src/", 1)[0] + "/src")

from evoloop.storage import SQLiteStorage
from evoloop.annotations import Annotation, AnnotationStorage, Judgment
from evoloop.types import Trace


# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="EvoLoop",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Clean header styling */
    .main-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #333;
    }
    
    /* Sidebar styling */
    .sidebar-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    /* Card styling */
    .trace-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Status badges */
    .badge-success {
        background: #22c55e20;
        color: #22c55e;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .badge-error {
        background: #ef444420;
        color: #ef4444;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .badge-pending {
        background: #f59e0b20;
        color: #f59e0b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 0.75rem;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Section headers */
    .section-header {
        font-size: 0.85rem;
        font-weight: 500;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #333;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def get_db_path() -> str:
    """Get database path from command line args or default."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="evoloop.db")
    args, _ = parser.parse_known_args()
    return args.db_path


def get_storages(db_path: str):
    """Get storage instances."""
    return SQLiteStorage(db_path), AnnotationStorage(db_path)


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar(trace_storage: SQLiteStorage, annotation_storage: AnnotationStorage):
    """Render the sidebar with filters and stats."""
    st.sidebar.markdown('<p class="sidebar-title">EvoLoop</p>', unsafe_allow_html=True)
    st.sidebar.caption("Trace Viewer")
    
    st.sidebar.divider()
    
    # Stats
    st.sidebar.markdown('<p class="section-header">Statistics</p>', unsafe_allow_html=True)
    
    total_traces = trace_storage.count()
    error_traces = trace_storage.count(status="error")
    total_annotations = annotation_storage.count()
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Traces", total_traces)
    col2.metric("Errors", error_traces)
    
    annotation_stats = annotation_storage.get_stats()
    if annotation_stats:
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Annotated", annotation_stats.get("total", 0))
        col2.metric("Pass Rate", f"{annotation_stats.get('pass_rate', 0):.1f}%")
    
    st.sidebar.divider()
    
    # Filters
    st.sidebar.markdown('<p class="section-header">Filters</p>', unsafe_allow_html=True)
    
    status_filter = st.sidebar.selectbox(
        "Status",
        ["All", "Success", "Error"],
        index=0,
    )
    
    annotation_filter = st.sidebar.selectbox(
        "Annotation Status",
        ["All", "Not Annotated", "Annotated", "Pass", "Fail"],
        index=0,
    )
    
    limit = st.sidebar.slider("Traces to load", 10, 500, 50)
    
    st.sidebar.divider()
    
    # Navigation
    st.sidebar.markdown('<p class="section-header">Navigation</p>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "Page",
        ["Traces", "Annotate", "Taxonomy", "Export"],
        label_visibility="collapsed",
    )
    
    return {
        "status": None if status_filter == "All" else status_filter.lower(),
        "annotation_filter": annotation_filter,
        "limit": limit,
        "page": page,
    }


# =============================================================================
# Traces Page
# =============================================================================

def render_traces_page(
    trace_storage: SQLiteStorage,
    annotation_storage: AnnotationStorage,
    filters: dict,
):
    """Render the traces list page."""
    st.markdown('<p class="main-header">Traces</p>', unsafe_allow_html=True)
    
    traces = trace_storage.list_traces(
        limit=filters["limit"],
        status=filters["status"],
    )
    
    if not traces:
        st.info("No traces found. Start monitoring your agent with @monitor")
        return
    
    # Filter by annotation status
    if filters["annotation_filter"] != "All":
        filtered_traces = []
        for trace in traces:
            annotations = annotation_storage.get_for_trace(trace.id)
            has_annotation = len(annotations) > 0
            
            if filters["annotation_filter"] == "Not Annotated" and not has_annotation:
                filtered_traces.append(trace)
            elif filters["annotation_filter"] == "Annotated" and has_annotation:
                filtered_traces.append(trace)
            elif filters["annotation_filter"] == "Pass" and has_annotation:
                if any(a.judgment == Judgment.PASS for a in annotations):
                    filtered_traces.append(trace)
            elif filters["annotation_filter"] == "Fail" and has_annotation:
                if any(a.judgment == Judgment.FAIL for a in annotations):
                    filtered_traces.append(trace)
        traces = filtered_traces
    
    st.caption(f"Showing {len(traces)} traces")
    
    for trace in traces:
        render_trace_card(trace, annotation_storage)


def render_trace_card(trace: Trace, annotation_storage: AnnotationStorage):
    """Render a single trace card."""
    annotations = annotation_storage.get_for_trace(trace.id)
    has_annotation = len(annotations) > 0
    
    # Status indicator
    if trace.status == "error":
        status_label = "ERROR"
        status_class = "badge-error"
    elif has_annotation:
        if any(a.judgment == Judgment.PASS for a in annotations):
            status_label = "PASS"
            status_class = "badge-success"
        else:
            status_label = "FAIL"
            status_class = "badge-error"
    else:
        status_label = "PENDING"
        status_class = "badge-pending"
    
    # Truncate input for title
    input_preview = str(trace.input)[:80] + "..." if len(str(trace.input)) > 80 else str(trace.input)
    
    with st.expander(f"[{status_label}] {input_preview}", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.caption(f"ID: `{trace.id[:8]}...` | {trace.timestamp}")
        
        with col2:
            if trace.duration_ms:
                st.caption(f"⏱️ {trace.duration_ms:.0f}ms")
        
        # Input
        st.markdown("**Input:**")
        st.code(str(trace.input), language="text")
        
        # Output
        st.markdown("**Output:**")
        st.code(str(trace.output), language="text")
        
        # Context (if exists)
        if trace.context and trace.context.data:
            st.markdown("**Context:**")
            st.json(trace.context.data)
        
        # Error (if exists)
        if trace.error:
            st.markdown("**Error:**")
            st.error(trace.error)
        
        # Existing annotation
        if has_annotation:
            st.markdown("---")
            st.markdown("**Annotation:**")
            for annotation in annotations:
                judgment_badge = "PASS" if annotation.is_pass else "FAIL"
                st.markdown(f"**{judgment_badge}** by `{annotation.annotator}`")
                st.info(annotation.critique)
                if annotation.tags:
                    st.markdown("Tags: " + ", ".join(f"`{t}`" for t in annotation.tags))


# =============================================================================
# Annotate Page
# =============================================================================

def render_annotate_page(
    trace_storage: SQLiteStorage,
    annotation_storage: AnnotationStorage,
    filters: dict,
):
    """Render the annotation page."""
    st.markdown('<p class="main-header">Annotate Traces</p>', unsafe_allow_html=True)
    
    # Get trace to annotate
    trace_id = st.session_state.get("annotate_trace_id")
    
    if not trace_id:
        # Show unannotated traces
        unannotated = annotation_storage.get_unannotated_traces(limit=filters["limit"])
        
        # Stats
        total_traces = trace_storage.count()
        annotated_count = annotation_storage.count()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Traces", total_traces)
        col2.metric("Annotated", annotated_count)
        col3.metric("Pending", len(unannotated))
        
        st.divider()
        
        if not unannotated:
            st.success("All traces have been annotated.")
            return
        
        st.subheader(f"Pending Annotation ({len(unannotated)})")
        
        # Show list with more info
        for tid in unannotated[:20]:
            trace = trace_storage.load(tid)
            if trace:
                status_label = "ERROR" if trace.status == "error" else "OK"
                input_preview = str(trace.input)[:50] + "..." if len(str(trace.input)) > 50 else str(trace.input)
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"[{status_label}] {input_preview}")
                with col2:
                    if st.button("Review", key=f"select_{tid}"):
                        st.session_state["annotate_trace_id"] = tid
                        st.rerun()
        return
    
    # Load trace
    trace = trace_storage.load(trace_id)
    if not trace:
        st.error("Trace not found!")
        if st.button("← Back"):
            st.session_state.pop("annotate_trace_id", None)
            st.rerun()
        return
    
    # Display trace
    st.subheader("Trace Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Input:**")
        st.code(str(trace.input), language="text")
    
    with col2:
        st.markdown("**Output:**")
        st.code(str(trace.output), language="text")
    
    # Context
    if trace.context and trace.context.data:
        with st.expander("Context (API/DB data)", expanded=True):
            st.json(trace.context.data)
    
    # Error
    if trace.error:
        st.error(f"**Error:** {trace.error}")
    
    st.divider()
    
    # Annotation form
    st.subheader("Your Annotation")
    
    st.markdown("""
    **Instructions:**
    1. **Binary judgment**: Did the AI achieve the desired outcome?
    2. **Critique**: Explain your reasoning in detail
    3. **Tags**: Add tags for failure taxonomy
    """)
    
    # Use form to prevent rerun on every input change
    with st.form(key=f"annotation_form_{trace_id}"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            judgment = st.radio(
                "Judgment",
                ["Pass", "Fail", "Skip"],
                index=None,
                help="Did the AI achieve the desired outcome?",
            )
        
        with col2:
            critique = st.text_area(
                "Critique",
                height=150,
                placeholder="Explain your reasoning in detail. Why did this pass or fail? "
                           "What specific issues did you observe? Be detailed enough that "
                           "someone unfamiliar with the system could understand.",
            )
        
        # Tags
        existing_tags = list(annotation_storage.get_failure_taxonomy().keys())
        
        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="wrong_discount, hallucination, missed_context",
            help="Add tags to build your failure taxonomy",
        )
        
        if existing_tags:
            st.caption("Existing tags: " + ", ".join(f"`{t}`" for t in existing_tags[:10]))
        
        annotator = st.text_input("Your name/email", value="default")
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("Save Annotation", type="primary")
        
        with col2:
            skipped = st.form_submit_button("Skip")
        
        with col3:
            back = st.form_submit_button("Back to list")
    
    # Debug: show form state
    st.caption(f"Debug: submitted={submitted}, judgment={judgment}, trace_id={trace_id[:8] if trace_id else None}")
    
    # Handle form submission outside the form
    if submitted:
        st.warning("Form was submitted!")  # Debug
        if not judgment:
            st.error("Please select a judgment (Pass, Fail, or Skip)")
        else:
            st.info(f"Saving: {judgment} for trace {trace_id[:8]}...")  # Debug
            # Parse tags
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            # Create annotation
            annotation = Annotation(
                trace_id=trace_id,
                judgment=Judgment(judgment.lower()),
                critique=critique,
                tags=tags,
                annotator=annotator,
            )
            
            # Save directly with explicit commit
            try:
                import sqlite3
                import json as json_lib
                db_path = get_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                data = annotation.to_dict()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO annotations 
                    (id, trace_id, judgment, critique, tags, annotator, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["id"],
                        data["trace_id"],
                        data["judgment"],
                        data["critique"],
                        json_lib.dumps(data["tags"]),
                        data["annotator"],
                        data["timestamp"],
                        json_lib.dumps(data["metadata"]) if data["metadata"] else None,
                    ),
                )
                conn.commit()
                conn.close()
                
                st.success(f"Annotation saved: {judgment}")
                
                import time
                time.sleep(1)  # Wait to ensure write completes
                
                # Go to next unannotated
                st.session_state.pop("annotate_trace_id", None)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save annotation: {e}")
    
    if skipped:
        st.session_state.pop("annotate_trace_id", None)
        st.rerun()
    
    if back:
        st.session_state.pop("annotate_trace_id", None)
        st.rerun()


# =============================================================================
# Taxonomy Page
# =============================================================================

def render_taxonomy_page(annotation_storage: AnnotationStorage):
    """Render the failure taxonomy page."""
    st.markdown('<p class="main-header">Failure Taxonomy</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Categorize failures into distinct groups to identify patterns and prioritize fixes.
    """)
    
    taxonomy = annotation_storage.get_failure_taxonomy()
    
    if not taxonomy:
        st.info("No failure tags yet. Start annotating traces to build your taxonomy.")
        return
    
    # Stats
    stats = annotation_storage.get_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Annotations", stats.get("total", 0))
    col2.metric("Pass Rate", f"{stats.get('pass_rate', 0):.1f}%")
    col3.metric("Unique Failure Types", len(taxonomy))
    
    st.divider()
    
    # Taxonomy chart
    st.subheader("Failure Distribution")
    
    import pandas as pd
    
    df = pd.DataFrame([
        {"Tag": tag, "Count": count}
        for tag, count in taxonomy.items()
    ])
    
    st.bar_chart(df.set_index("Tag"))
    
    # Table
    st.subheader("Failure Details")
    st.dataframe(df, use_container_width=True)
    
    # Drill-down
    st.divider()
    st.subheader("Explore by Tag")
    
    selected_tag = st.selectbox("Select a tag to see examples", list(taxonomy.keys()))
    
    if selected_tag:
        annotations = annotation_storage.list_annotations(tag=selected_tag, limit=10)
        
        st.caption(f"Showing {len(annotations)} examples with tag `{selected_tag}`")
        
        for annotation in annotations:
            with st.expander(f"Trace: {annotation.trace_id[:8]}..."):
                st.markdown(f"**Critique:** {annotation.critique}")


# =============================================================================
# Export Page
# =============================================================================

def render_export_page(
    trace_storage: SQLiteStorage,
    annotation_storage: AnnotationStorage,
):
    """Render the export page."""
    st.markdown('<p class="main-header">Export Data</p>', unsafe_allow_html=True)
    
    from evoloop.export import (
        export_traces_to_csv,
        export_annotations_to_csv,
        export_traces_to_json,
        export_annotations_to_json,
    )
    from evoloop.export.json_export import export_for_judge_training
    import io
    
    st.subheader("Traces")
    
    col1, col2 = st.columns(2)
    
    with col1:
        trace_format = st.selectbox("Format", ["CSV", "JSON"], key="trace_format")
        trace_limit = st.number_input("Limit", 100, 100000, 1000, key="trace_limit")
    
    with col2:
        trace_status = st.selectbox(
            "Status Filter",
            ["All", "Success", "Error"],
            key="trace_status",
        )
    
    if st.button("Export Traces"):
        buffer = io.StringIO()
        status = None if trace_status == "All" else trace_status.lower()
        
        if trace_format == "CSV":
            count = export_traces_to_csv(buffer, trace_storage, limit=trace_limit, status=status)
            filename = "traces.csv"
            mime = "text/csv"
        else:
            count = export_traces_to_json(buffer, trace_storage, limit=trace_limit, status=status)
            filename = "traces.json"
            mime = "application/json"
        
        st.download_button(
            f"Download ({count} traces)",
            buffer.getvalue(),
            filename,
            mime,
        )
    
    st.divider()
    
    st.subheader("Annotations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ann_format = st.selectbox("Format", ["CSV", "JSON"], key="ann_format")
        ann_limit = st.number_input("Limit", 100, 100000, 1000, key="ann_limit")
    
    with col2:
        ann_judgment = st.selectbox(
            "Judgment Filter",
            ["All", "Pass", "Fail"],
            key="ann_judgment",
        )
        include_traces = st.checkbox("Include trace data", key="include_traces")
    
    if st.button("Export Annotations"):
        buffer = io.StringIO()
        judgment = None if ann_judgment == "All" else ann_judgment.lower()
        
        if ann_format == "CSV":
            count = export_annotations_to_csv(
                buffer, annotation_storage,
                limit=ann_limit, judgment=judgment,
                include_trace_data=include_traces,
                trace_storage=trace_storage if include_traces else None,
            )
            filename = "annotations.csv"
            mime = "text/csv"
        else:
            count = export_annotations_to_json(
                buffer, annotation_storage,
                limit=ann_limit, judgment=judgment,
                include_trace_data=include_traces,
                trace_storage=trace_storage if include_traces else None,
            )
            filename = "annotations.json"
            mime = "application/json"
        
        st.download_button(
            f"Download ({count} annotations)",
            buffer.getvalue(),
            filename,
            mime,
        )
    
    st.divider()
    
    st.subheader("Judge Training Data")
    
    st.markdown("""
    Export annotations in a format optimized for training an LLM-as-Judge.
    Includes balanced pass/fail examples with full trace context.
    """)
    
    if st.button("Export Judge Training Data"):
        buffer = io.StringIO()
        count = export_for_judge_training(buffer, annotation_storage, trace_storage)
        
        st.download_button(
            f"Download ({count} examples)",
            buffer.getvalue(),
            "judge_training_data.json",
            "application/json",
        )


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main application entry point."""
    db_path = get_db_path()
    trace_storage, annotation_storage = get_storages(db_path)
    
    # Render sidebar and get filters
    filters = render_sidebar(trace_storage, annotation_storage)
    
    # Override page if set in session state
    if "page" in st.session_state:
        page = st.session_state.pop("page")
        if page == "annotate":
            filters["page"] = "Annotate"
    
    # Render selected page
    if filters["page"] == "Traces":
        render_traces_page(trace_storage, annotation_storage, filters)
    elif filters["page"] == "Annotate":
        render_annotate_page(trace_storage, annotation_storage, filters)
    elif filters["page"] == "Taxonomy":
        render_taxonomy_page(annotation_storage)
    elif filters["page"] == "Export":
        render_export_page(trace_storage, annotation_storage)


if __name__ == "__main__":
    main()
