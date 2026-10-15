"""
MeetMind AI - AI Meeting Action-Item Extractor
app.py: Streamlit web application providing a professional, modern interface
for converting meeting transcripts into structured action items.
"""

import os
import json
from datetime import datetime, date
import pandas as pd
import streamlit as st

import meeting_extractor as me

# Set page configuration with a modern professional layout
st.set_page_config(
    page_title="MeetMind AI - Action-Item Extractor",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern navy/blue aesthetic, clean typography, and rounded cards
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Header typography */
    .app-title {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A; /* Deep Navy */
        margin-bottom: 0.2rem;
    }
    
    .app-subtitle {
        font-size: 1.05rem;
        color: #475569; /* Slate Gray */
        margin-bottom: 1.2rem;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .status-badge-ready {
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
    }
    .status-badge-missing {
        background-color: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }
    .status-badge-success {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
    }
    
    /* Summary Metric Cards */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.85rem;
        font-weight: 700;
        color: #1E3A8A; /* Navy */
        margin-bottom: 0.2rem;
    }
    .metric-lbl {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Summary box */
    .summary-box {
        background-color: #FFFFFF;
        border-left: 4px solid #2563EB;
        border-radius: 6px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
    }
    .summary-heading {
        font-weight: 700;
        color: #1E3A8A;
        font-size: 1.05rem;
        margin-bottom: 0.4rem;
    }
    .summary-text {
        color: #334155;
        font-size: 0.96rem;
        line-height: 1.5;
    }
    
    /* Evidence card */
    .evidence-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .evidence-quote {
        font-style: italic;
        color: #475569;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state keys
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None
if "api_call_status" not in st.session_state:
    st.session_state.api_call_status = "idle"  # 'idle', 'in_progress', 'completed', 'failed'
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


def load_sample_transcript():
    """Load text from sample_transcript.txt into the session state."""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_transcript.txt")
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            st.session_state.transcript_text = f.read()
            st.session_state.extraction_result = None
            st.session_state.api_call_status = "idle"
    else:
        st.session_state.transcript_text = (
            "Meeting date: October 14, 2026\n\n"
            "Priya: We need to finish the dashboard design by October 18.\n"
            "Rahul: I will complete the API integration by October 20.\n"
            "Priya: Rahul, please share the integration progress with the team tomorrow.\n"
            "Amit: I will prepare the testing checklist by October 19.\n"
            "Priya: Someone needs to arrange the next client review, but we haven't assigned an owner yet.\n"
            "Rahul: The login page is already completed."
        )


# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Settings & API")
    
    env_api_key = me.get_configured_api_key()
    env_model = me.get_configured_model()
    
    user_api_key = st.text_input(
        "Gemini API Key",
        value=env_api_key if env_api_key else "",
        type="password",
        help="Reads automatically from .env if present, or enter key here securely."
    )
    
    selected_model = st.text_input(
        "Gemini Model Name",
        value=env_model,
        help="Configurable Gemini model (e.g. gemini-2.5-flash, gemini-1.5-pro)."
    )
    
    st.markdown("---")
    
    # Truthful status indicator: Configured vs Not Configured vs Call Succeeded
    is_key_set, status_msg = me.check_api_configuration(user_api_key)
    
    if not is_key_set:
        st.markdown(
            '<div class="status-badge status-badge-missing">⚠️ API Key: Not Configured</div>',
            unsafe_allow_html=True
        )
        st.info("Obtain a free Google Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey).")
    else:
        if st.session_state.api_call_status == "completed":
            st.markdown(
                '<div class="status-badge status-badge-success">● Connected & Verified (Last call OK)</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-badge status-badge-ready">○ Key Configured (Awaiting Call)</div>',
                unsafe_allow_html=True
            )
            
    st.caption("Note: 'Configured' confirms an API key is present. The connection is tested upon initiating extraction.")
    
    st.markdown("---")
    st.markdown("### 📖 About MeetMind AI")
    st.markdown(
        "MeetMind AI uses Google's Gemini LLM to extract actionable commitments from meeting dialogues. "
        "It validates required fields, flags missing owners and deadlines, detects duplicates, "
        "and allows inline review and export."
    )


# Main Header
st.markdown('<div class="app-title">MeetMind AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Turn meeting conversations into clear, actionable tasks.</div>', unsafe_allow_html=True)

# ----------------- Input Section -----------------
st.markdown("#### 1. Supply Meeting Transcript")

col_actions1, col_actions2 = st.columns([1, 4])
with col_actions1:
    if st.button("📄 Load Sample Transcript", use_container_width=True, help="Load an example transcript immediately"):
        load_sample_transcript()
        st.rerun()

uploaded_file = st.file_uploader(
    "Or upload a transcript file (.txt)",
    type=["txt"],
    help="Upload a standard UTF-8 encoded text transcript"
)

if uploaded_file is not None:
    try:
        file_content = uploaded_file.read().decode("utf-8")
        if file_content != st.session_state.transcript_text:
            st.session_state.transcript_text = file_content
            st.session_state.extraction_result = None
            st.session_state.api_call_status = "idle"
            st.success(f"Loaded '{uploaded_file.name}' successfully.")
    except Exception as e:
        st.error(f"Error reading uploaded file: {str(e)}")

# Text area for transcript
transcript_input = st.text_area(
    "Transcript Content:",
    value=st.session_state.transcript_text,
    height=220,
    placeholder="Paste or type meeting dialogue here (e.g. Priya: We need to finish the dashboard design by October 18...)"
)

# Keep session state updated with text area edits
st.session_state.transcript_text = transcript_input

# Meeting Date Reference option
col_date_opt, col_date_picker = st.columns([1, 2])
with col_date_opt:
    use_meeting_date = st.checkbox("Provide reference meeting date", value=True, help="Helps resolve relative dates like 'tomorrow' or 'next Monday'")

meeting_date_val = None
if use_meeting_date:
    with col_date_picker:
        selected_date = st.date_input(
            "Meeting Date",
            value=date(2026, 10, 14),
            help="Reference date for calculating relative deadlines"
        )
        meeting_date_val = selected_date.strftime("%Y-%m-%d")

# Extraction Trigger
col_btn, col_empty = st.columns([1, 3])
with col_btn:
    extract_clicked = st.button(
        "⚡ Extract Action Items",
        type="primary",
        disabled=st.session_state.is_processing,
        use_container_width=True
    )

# ----------------- Extraction Processing -----------------
if extract_clicked:
    if not transcript_input or not transcript_input.strip():
        st.warning("⚠️ Please provide a transcript by pasting text, uploading a file, or clicking 'Load Sample Transcript'.")
    elif not is_key_set:
        st.error("⚠️ Google Gemini API key is required. Enter it in the left sidebar or define GEMINI_API_KEY in your .env file.")
    else:
        st.session_state.is_processing = True
        st.session_state.api_call_status = "in_progress"
        
        with st.spinner("Extracting action items with Google Gemini..."):
            result = me.extract_action_items(
                transcript=transcript_input,
                meeting_date=meeting_date_val,
                api_key=user_api_key,
                model_name=selected_model
            )
            
        st.session_state.is_processing = False
        
        if result["success"]:
            st.session_state.extraction_result = result
            st.session_state.api_call_status = "completed"
            st.success("Action items extracted and validated successfully!")
            st.rerun()
        else:
            st.session_state.extraction_result = None
            st.session_state.api_call_status = "failed"
            st.error(f"Extraction failed: {result['error']}")

# ----------------- Results Dashboard -----------------
if st.session_state.extraction_result and st.session_state.extraction_result.get("success"):
    res = st.session_state.extraction_result
    action_items = res.get("action_items", [])
    summary = res.get("meeting_summary", "No summary provided.")
    
    st.markdown("---")
    st.markdown("#### 2. Meeting Summary")
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-heading">Executive Overview</div>
        <div class="summary-text">{summary}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate Metrics
    total_tasks = len(action_items)
    assigned_tasks = sum(1 for item in action_items if item.get("owner", "Unassigned") != "Unassigned")
    unassigned_tasks = total_tasks - assigned_tasks
    tasks_with_deadline = sum(1 for item in action_items if item.get("deadline") and item.get("deadline") != "Not specified")
    
    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{total_tasks}</div>
            <div class="metric-lbl">Total Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{assigned_tasks}</div>
            <div class="metric-lbl">Assigned</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color: {'#B91C1C' if unassigned_tasks > 0 else '#1E3A8A'};">{unassigned_tasks}</div>
            <div class="metric-lbl">Unassigned</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{tasks_with_deadline}</div>
            <div class="metric-lbl">With Deadlines</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Table & Editable Grid
    st.markdown("#### 3. Structured Action Items (Review & Edit)")
    st.caption("You can edit tasks, owners, deadlines, status, or confidence scores directly in the table below before exporting.")
    
    if total_tasks == 0:
        st.info("No actionable tasks were identified in this transcript.")
    else:
        # Build pandas DataFrame for display and editing
        table_rows = []
        for idx, item in enumerate(action_items, 1):
            warn_str = " | ".join(item.get("warnings", [])) if item.get("warnings") else "None"
            table_rows.append({
                "ID": idx,
                "Task": item.get("task", ""),
                "Owner": item.get("owner", "Unassigned"),
                "Deadline": item.get("deadline") if item.get("deadline") else "Not specified",
                "Status": item.get("status", "Pending"),
                "Confidence (%)": item.get("confidence", 80),
                "Review Warnings": warn_str
            })
            
        df_tasks = pd.DataFrame(table_rows)
        
        # Interactive data editor
        edited_df = st.data_editor(
            df_tasks,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "Task": st.column_config.TextColumn("Task Description", width="large", required=True),
                "Owner": st.column_config.TextColumn("Owner", width="medium"),
                "Deadline": st.column_config.TextColumn("Deadline (YYYY-MM-DD)", width="medium"),
                "Status": st.column_config.SelectboxColumn("Status", options=["Pending", "In Progress", "Completed"], width="medium"),
                "Confidence (%)": st.column_config.NumberColumn("Confidence (%)", min_value=0, max_value=100, width="small"),
                "Review Warnings": st.column_config.TextColumn("Review Warnings", disabled=True, width="large")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # Supporting Evidence Accordion
        with st.expander("🔍 View Supporting Evidence Quotes from Transcript", expanded=False):
            for idx, item in enumerate(action_items, 1):
                st.markdown(f"""
                <div class="evidence-card">
                    <strong>Task #{idx}:</strong> {item.get('task')}<br>
                    <strong>Owner:</strong> {item.get('owner', 'Unassigned')} | <strong>Deadline:</strong> {item.get('deadline', 'Not specified')}<br>
                    <span class="evidence-quote">Evidence: "{item.get('evidence', 'No quote')}"</span>
                </div>
                """, unsafe_allow_html=True)
                
        # Export Actions
        st.markdown("#### 4. Export Action Items")
        exp_col1, exp_col2, _ = st.columns([1, 1, 2])
        
        # Prepare exports based on currently edited data
        edited_records = edited_df.to_dict(orient="records")
        
        # Format CSV
        csv_data = edited_df.to_csv(index=False).encode("utf-8")
        
        # Format JSON with summary and edited items
        export_json_obj = {
            "meeting_summary": summary,
            "total_action_items": len(edited_records),
            "extracted_at": datetime.now().isoformat(),
            "action_items": [
                {
                    "task": r["Task"],
                    "owner": r["Owner"],
                    "deadline": None if r["Deadline"] in ["Not specified", "", "None"] else r["Deadline"],
                    "status": r["Status"],
                    "confidence": r["Confidence (%)"],
                    "review_warnings": [w.strip() for w in r["Review Warnings"].split("|")] if r["Review Warnings"] != "None" else []
                }
                for r in edited_records
            ]
        }
        json_data = json.dumps(export_json_obj, indent=2).encode("utf-8")
        
        with exp_col1:
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="meeting_action_items.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with exp_col2:
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name="meeting_action_items.json",
                mime="application/json",
                use_container_width=True
            )

elif st.session_state.api_call_status == "idle" and not st.session_state.transcript_text:
    # Clean Empty State
    st.markdown("---")
    st.info(
        "👋 **Welcome to MeetMind AI!**\n\n"
        "To get started:\n"
        "1. Click **'📄 Load Sample Transcript'** above or paste your own meeting conversation.\n"
        "2. Ensure your Gemini API Key is configured in the left sidebar or `.env` file.\n"
        "3. Click **'⚡ Extract Action Items'** to generate structured, actionable tasks."
    )
