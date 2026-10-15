# MeetMind AI: AI Meeting Action-Item Extractor

**Turn meeting conversations into clear, actionable tasks.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Google Gen AI SDK](https://img.shields.io/badge/LLM-Google%20Gen%20AI%20SDK-4285F4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Project Overview & Problem Statement

In modern professional and academic settings, team meetings, standups, and client syncs produce a high volume of conversational transcripts. Crucial commitments, task assignments, and deadlines often get lost in unstructured dialogue, resulting in missed deadlines and unassigned responsibilities.

**MeetMind AI** is an AI-powered meeting action-item extractor built with **Streamlit** and the official **Google Gen AI Python SDK**. It analyzes conversational transcripts, filters conversational noise, and outputs structured action items containing:
- **Task description**
- **Owner** (or clearly labeled as `Unassigned`)
- **Deadline** (in standardized ISO `YYYY-MM-DD` format or flagged as relative/unspecified)
- **Status** (`Pending`, `In Progress`, or `Completed`)
- **Confidence score** (0–100%)
- **Supporting evidence quote** directly from the transcript dialogue

---

## 2. Key Features

- **Dual Transcript Ingestion**: Paste transcripts directly or upload `.txt` transcript files.
- **One-Click Sample Loader**: Instant demonstration with a built-in realistic meeting transcript.
- **Prompt Injection Defense**: Treats meeting transcripts strictly as untrusted data; commands embedded in meeting dialogue cannot override extraction rules.
- **Strict Schema Enforcement**: Requests and validates JSON responses using Gemini structured output and regex/ISO datetime validators.
- **Intelligent Duplicate Detection**: Compares task descriptions using `difflib` string similarity and token set ratios without silently deleting items, allowing users to review potential duplicates.
- **Relative Date Resolution**: Resolves relative dates (e.g., "tomorrow", "next Monday") when an optional meeting reference date is supplied, or preserves them with review flags if unconfirmed.
- **Audit & Review Warnings**: Automatically tags items with warnings (`Missing owner`, `No deadline`, `Relative deadline`, `Possible duplicate`, or `Low confidence`).
- **Interactive Data Editor**: Users can modify tasks, reassign owners, adjust deadlines, and alter statuses directly in an editable grid before exporting.
- **Multi-Format Export**: One-click download of reviewed items as **CSV** or structured **JSON** (including executive summary and metadata).
- **Truthful AI Connection State**: Distinguishes local key configuration from active, verified API connectivity.

---

## 3. Technology Stack

- **Language**: Python 3.10+
- **User Interface**: Streamlit
- **LLM Engine**: Google Gemini API via official `google-genai` Python SDK
- **Data Processing**: Pandas
- **Validation**: Python standard library (`datetime`, `re`, `difflib`, `json`)
- **Environment Management**: `python-dotenv`

---

## 4. Project Folder Structure

```
AI_Meeting_Action_Item_Extractor/
├── app.py                   # Streamlit web application & UI layer
├── meeting_extractor.py     # Gemini client, extraction prompt, validation & duplicate detection
├── test_suite.py            # Unit test suite verifying validation and edge cases
├── sample_transcript.txt    # Built-in sample meeting dialogue for quick evaluation
├── requirements.txt         # Core project dependencies
├── .env.example             # Placeholder environment variables template
├── .gitignore               # Ignores .env, secrets, virtual environments, and caches
├── README.md                # Comprehensive project documentation
├── PROJECT_REPORT.md        # Formal internship academic report
└── screenshots/             # Interface screenshots and documentation
    └── README.md
```

---

## 5. Installation & Setup (Windows)

### Step 1: Open Terminal and Navigate to Project
Open PowerShell or Command Prompt:
```powershell
cd "c:\Users\Admin\OneDrive\Desktop\AI Meeting Action-Item Extractor"
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 6. Google Gemini API Configuration

1. Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Create a local `.env` file by copying `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Edit `.env` and set your key and preferred model:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
   *(Alternatively, you can securely enter the API key directly in the sidebar inside the running Streamlit web application).*

---

## 7. Running the Application

Execute the Streamlit application:
```powershell
streamlit run app.py
```

The application will launch in your default browser at `http://localhost:8501`.

---

## 8. Example Usage Walkthrough

1. **Load Transcript**: Click the **"📄 Load Sample Transcript"** button or paste your own meeting notes.
2. **Set Reference Date**: Keep or modify the reference date (e.g., `2026-10-14`) to allow relative terms such as "tomorrow" to calculate into exact calendar dates.
3. **Run Extraction**: Click **"⚡ Extract Action Items"**.
4. **Review Dashboard**:
   - Read the executive meeting summary.
   - Inspect summary cards (`Total Tasks`, `Assigned`, `Unassigned`, `With Deadlines`).
   - Examine the editable grid for flagged warnings (e.g., tasks marked `Unassigned` or possible duplicates).
5. **Inspect Evidence**: Expand the "View Supporting Evidence Quotes" drawer to inspect verbatim source dialogue.
6. **Export**: Click **"📥 Download CSV"** or **"📥 Download JSON"** to save your finalized task list.

---

## 9. Testing & Quality Assurance Checklist

You can execute the automated test suite anytime using:
```powershell
python -m unittest test_suite.py -v
```

| Test Case | Description | Expected Result | Status |
|---|---|---|---|
| **Empty Input** | Transcript text is empty or spaces | Clear validation error; no API call | Passed |
| **Short Input** | Transcript has < 15 characters | Flagged as too short; rejected | Passed |
| **Unassigned Owner** | Task without assigned person | Owner set to `Unassigned` with warning | Passed |
| **Missing Deadline** | Action item lacks explicit date | Set to `Not specified` / `null` with warning | Passed |
| **ISO Date Format** | Explicit calendar dates | Validated against `YYYY-MM-DD` | Passed |
| **Completed Work** | Dialogue indicates work finished | Status preserved as `Completed` | Passed |
| **Relative Deadlines** | Words like "tomorrow" with reference date | Resolved or flagged for user review | Passed |
| **Duplicate Detection** | Two nearly identical tasks | Similarity calculated and flagged on both; not deleted | Passed |
| **Export Verification** | CSV & JSON download | Reflects user edits from `st.data_editor` | Passed |
| **API Authentication Guard** | Missing or placeholder key | User-friendly message prompting key input | Passed |

---

## 10. Security Guidance & Best Practices

- **Never Commit Secrets**: Ensure `.env` and `.streamlit/secrets.toml` remain in `.gitignore`.
- **Placeholder Values**: `.env.example` contains only placeholder strings.
- **Untrusted Input Sanitation**: Meeting transcripts are treated as untrusted data in the LLM system prompt to prevent jailbreaks or prompt injection attacks.
- **Zero Raw Tracebacks**: Exceptions (network timeout, quota limits, JSON parsing errors) are trapped and presented with clean, actionable user feedback.

---

## 11. Limitations & Future Scope

- **Audio/Video Ingestion**: Future releases could integrate automatic speech-to-text (Whisper / Gemini Multimodal audio input) to process recordings directly.
- **Project Management Sync**: Direct webhook export to Jira, Trello, Asana, or GitHub Issues.
- **Speaker Diarization**: Automated speaker mapping when transcripts lack explicit speaker labels.
