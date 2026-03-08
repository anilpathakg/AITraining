# 🏥 Anil Pathak's — Agentic Healthcare Assistant
### Capstone Project — Agentic Healthcare Assistant for Medical Task Automation

---

## 📋 Project Overview

This project is an **Agentic AI-powered Healthcare Assistant** built as a capstone project.
It combines Large Language Models (GPT-4o-mini), Retrieval-Augmented Generation (RAG),
and a multi-tool agentic framework to automate common healthcare tasks such as patient
record management, appointment booking, medical history retrieval, and trusted medical
information search.

The system is built using **LangChain**, **OpenAI GPT-4o-mini**, **FAISS vector store**,
and **Streamlit** for the user interface, with full **LLMOps monitoring** including
interaction logging, tool usage analytics, and LLM-as-judge evaluation.

---

## 👨‍💻 Submission Details

| Field | Details |
|---|---|
| **Submitted by** | Anil Pathak |
| **Project Type** | Capstone Project |
| **Project Title** | Agentic Healthcare Assistant for Medical Task Automation |
| **AI Coding Assistant** | Claude (Anthropic) |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  Home · Patient Dashboard · Doctor Dashboard · Chat · Eval  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Healthcare Agent (agent.py)                     │
│         GPT-4o-mini + Function Calling (13 tools)           │
│              Sliding Window Memory + Patient Context         │
└──┬────────────┬──────────────┬──────────────┬───────────────┘
   │            │              │              │
┌──▼──┐    ┌───▼───┐    ┌─────▼────┐   ┌────▼────────┐
│ DB  │    │  API  │    │   RAG    │   │   Medical   │
│Tools│    │ Tools │    │  Tools   │   │   Search    │
│     │    │       │    │          │   │             │
│Patient   │Doctor │    │FAISS +   │   │MedlinePlus  │
│Records   │Schedule    │PDF       │   │WHO + DDG    │
│xlsx │    │xlsx   │    │Reports   │   │fallback     │
└─────┘    └───────┘    └──────────┘   └─────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  LLMOps Layer                                │
│       Logger · Evaluator · Analytics Dashboard              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### Patient Section
- **Patient Search** — Search records by name or ID, view appointments
- **Doctor Search** — Find doctors by specialty, view profiles
- **My Appointments** — Book and cancel appointments (name-based, no IDs required)
- **Medical History RAG** — AI-generated summaries from PDF reports using FAISS

### Doctor / Admin Section
- **Doctor Schedule** — View full appointment schedule by doctor name
- **Medical Records** — Add new patients, update structured and unstructured fields
- **Model Evaluation** — LLM-as-judge scoring across 8 predefined test cases
- **Logs & Analytics** — Tool usage, booking success rate, module KPIs

### AI Chat Assistant
- Natural language interface for all healthcare tasks
- GPT-4o-mini with 13 function-calling tools
- Conversation memory with sliding window
- Active patient context tracking

### Medical Information Search
- **Primary**: MedlinePlus (NLM/NIH) API
- **Secondary**: WHO Health Topics
- **Fallback**: DuckDuckGo (only if trusted sources return nothing)

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| LLM | OpenAI GPT-4o-mini |
| Agent Framework | LangChain 1.2.x + OpenAI Function Calling |
| Vector Store | FAISS (Facebook AI Similarity Search) |
| Embeddings | OpenAI text-embedding-3-small |
| UI Framework | Streamlit |
| Patient Data | Excel (records.xlsx) via pandas |
| Doctor Schedule | Mock API (doctors.xlsx) |
| Medical Search | MedlinePlus API + WHO + DuckDuckGo |
| LLMOps | Custom Logger + LLM-as-Judge Evaluator |
| Environment | Python 3.11+ |

---

## 📁 Project Structure

```
healthcare_assistant/
│
├── streamlit_app.py              # Main entry point — home page + role selector
├── agent.py                      # Core agent orchestrator (GPT-4o-mini + 13 tools)
├── config.py                     # Central path configuration
├── requirements.txt              # Python dependencies
│
├── .streamlit/
│   └── config.toml               # Hides auto-generated Streamlit nav
│
├── pages/                        # Streamlit pages
│   ├── 0_Patient_Dashboard.py    # Patient section hub (4 cards)
│   ├── 0_Doctor_Dashboard.py     # Doctor/Admin section hub (5 cards)
│   ├── 1_Patient_Search.py       # Patient search + RAG history
│   ├── 2_Doctor_Search.py        # Find doctors by specialty
│   ├── 3_My_Appointments.py      # Book + cancel appointments
│   ├── 4_Doctor_Schedule.py      # Doctor's appointment schedule
│   ├── 5_Medical_Records.py      # Add/update patient records
│   ├── 6_Model_Evaluation.py     # LLM-as-judge evaluation suite
│   ├── 7_Logs_Analytics.py       # LLMOps monitoring dashboard
│   └── 8_Chat_Assistant.py       # Natural language chat interface
│
├── tools/                        # Agent tool functions
│   ├── patient_db_tool.py        # Patient CRUD (records.xlsx)
│   ├── appointment_tool.py       # Booking + scheduling
│   ├── rag_tool.py               # FAISS RAG pipeline
│   └── medical_search_tool.py    # MedlinePlus + WHO search
│
├── api/
│   └── doctor_schedule_api.py    # Mock doctor scheduling API
│
├── memory/
│   └── memory_module.py          # Sliding window + patient context
│
├── prompts/
│   └── system_prompts.py         # Agent system prompt templates
│
├── evaluation/
│   ├── evaluator.py              # LLM-as-judge (8 test cases)
│   └── logger.py                 # Interaction + tool call logger
│
├── utils/
│   ├── sidebar_helper.py         # Contextual sidebar renderer
│   └── card_helper.py            # Dashboard card renderer
│
├── data/
│   ├── records.xlsx              # Patient records (Patient_ID, Name, etc.)
│   ├── doctors.xlsx              # Doctor master data
│   ├── interaction_logs.json     # LLMOps log store (auto-generated)
│   └── reports/                  # Patient PDF reports for RAG
│       ├── sample_report_anjali.pdf
│       ├── sample_report_david.pdf
│       └── sample_report_ramesh.pdf
│
└── vector_store/
    └── patient_reports/          # FAISS index (auto-generated on first run)
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.11 or higher
- OpenAI API key

### 2. Clone / Download the Project
```bash
cd "C:\healthcare_assistant"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Set Up Data
Ensure the following files exist in the `data/` folder:
- `records.xlsx` — Patient records with `Patient_ID` column (P001, P002 ...)
- `doctors.xlsx` — Doctor master data
- `reports/` — Patient PDF reports for RAG

To regenerate sample data:
```bash
python setup_data.py
```

### 6. Run the Application
```bash
python -m streamlit run streamlit_app.py
```

Open your browser at: **http://localhost:8501**

---

## 🚀 Usage Guide

### As a Patient
1. Click **"Enter Patient Section"** on the home page
2. Use **Patient Search** to find your record
3. Use **Doctor Search** to browse doctors by specialty
4. Use **My Appointments** to book or cancel appointments
5. Use **Chat Assistant** for natural language queries

### As a Doctor / Admin
1. Click **"Enter Doctor / Admin Section"** on the home page
2. Use **Doctor Schedule** to view appointments by doctor name
3. Use **Medical Records** to add or update patient records
4. Use **Model Evaluation** to run the LLM-as-judge test suite
5. Use **Logs & Analytics** to monitor system performance

---

## 📊 LLMOps Evaluation

The system includes a built-in evaluation framework:

### Metrics Tracked
| Metric | Description |
|---|---|
| Relevance | Does the response address the query? |
| Accuracy | Is the medical information correct? |
| Completeness | Are all aspects of the query covered? |
| Clarity | Is the response well-structured? |
| Safety | Does it recommend professional consultation? |
| Booking Success Rate | % of successful appointment bookings |
| Tool Selection Accuracy | Did the agent pick the right tool? |

### 8 Predefined Test Cases
| ID | Category |
|---|---|
| TC001 | Patient Lookup |
| TC002 | Medical History RAG |
| TC003 | Medical History RAG |
| TC004 | Appointment Booking |
| TC005 | Medical Information Search |
| TC006 | Medical Information Search |
| TC007 | Patient Lookup |
| TC008 | Multi-step reasoning |

---

## 🔒 Key Design Decisions

- **No IDs exposed to users** — Doctor IDs and Patient IDs are resolved internally
- **Trusted medical sources** — MedlinePlus and WHO are primary; DuckDuckGo is fallback only
- **Absolute log paths** — Uses `config.py` so logging works correctly under Streamlit
- **Role-based navigation** — Contextual sidebar adapts based on patient vs admin role
- **Direct booking logging** — `appointment_tool.py` logs bookings directly so success rate is captured from both UI and agent calls

---

## 📦 Requirements

Key packages (see `requirements.txt` for full list):

```
openai>=1.0.0
langchain>=0.1.0
langchain-openai
langchain-community
faiss-cpu
streamlit>=1.35.0
pandas
openpyxl
pypdf
python-dotenv
ddgs
```

---

## 📝 Notes

- The FAISS vector store is built automatically on first run from PDFs in `data/reports/`
- Interaction logs are stored in `data/interaction_logs.json`
- The doctor schedule API is an in-memory mock — bookings reset on app restart
- All pages include the standard project header and full docstring documentation

---

*Submitted by Anil Pathak | Generated with Claude (Anthropic) AI Coding Assistant*
