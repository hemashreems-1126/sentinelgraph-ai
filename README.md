# SentinelGraph — Multi-Agent Financial Crime Alert Investigation Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B.svg)](https://github.com/langchain-ai/langgraph)
[![Groq LLM](https://img.shields.io/badge/LLM-Groq%20(LLaMA--3.3)--F55036.svg)](https://groq.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose%20%26%20Render-2496ED.svg?logo=docker&logoColor=white)](https://render.com)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-10B981.svg)]()

> **SentinelGraph** is an enterprise-grade agentic financial crime investigation platform engineered for the **Razorpay AI Buildathon 2026 ("AI Risk Manager" track)**. It automates the full AML/fraud triage and investigation lifecycle across **11 cohesive stages**: from synthetic financial graph simulation and dual anomaly detection (Rule + Isolation Forest) to a multi-agent LangGraph workflow featuring static/adaptive planning, hypothesis formulation, 6 specialized investigative sub-agents, **100% deterministic Python risk scoring**, immutable cryptographic audit logging (SHA-256), and FinCEN-compliant Suspicious Activity Report (SAR) drafting with an active investigator feedback loop.

---

## Architecture Diagram

![SentinelGraph 11-Stage Architecture](docs/architecture_diagram.png)

---

## 🚀 How to Run in VS Code (Zero Docker Required)

If you are a recruiter, reviewer, or developer reviewing this project in **Visual Studio Code**, you do **NOT** need Docker, external databases, or paid API keys. Everything runs out of the box with zero setup!

### Step-by-Step in VS Code:

1. **Open the Project in VS Code**:
   - `File` $\to$ `Open Folder...` $\to$ select the cloned `sentinelgraph-ai` directory.

2. **Launch the Backend & Frontend**:
   - **On Windows**:
     - In VS Code Terminal 1: run `.\run_backend.bat`
     - In VS Code Terminal 2: run `.\run_frontend.bat`
   - **On macOS / Linux**:
     - In VS Code Terminal 1: run `./run_backend.sh`
     - In VS Code Terminal 2: run `./run_frontend.sh`

   *(Or press `Ctrl + Shift + B` in VS Code to run the automated VS Code Build Task that starts both automatically).*

3. **Open in Your Browser**:
   - 🌐 **Interactive Web Dashboard**: **[http://localhost:3000](http://localhost:3000)**
   - 📑 **Interactive Backend OpenAPI Docs**: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 💡 Quick Demo Walkthrough for Evaluators

1. **Seed Ledger**: Open **[http://localhost:3000](http://localhost:3000)** and click the purple **"Generate Synthetic Batch"** button on the Dashboard. This simulates 200 customer entities and 1,500 transactions, injecting 5 fraud topologies and flagging anomalies via Rule heuristics + Isolation Forest ML.
2. **Triage Queue**: Click **Alerts Queue** in the left sidebar $\to$ click **"Prioritize Queue"** to sort alerts by risk urgency $\to$ pick **Static Plan** or **Adaptive Planner** $\to$ click **"Investigate"**.
3. **Inspect Multi-Agent Dossier**:
   - **Full Agent Trail**: Click each step card to inspect per-agent inputs, outputs, and execution duration in milliseconds.
   - **Sub-Agent Evidence & Graph**: Explore the interactive 2-hop NetworkX entity network and behavioral z-score analytics.
   - **Deterministic Risk Score**: View the exact 0–100 mathematical score and policy action (`ALLOW`, `REVIEW`, `BLOCK`). Zero LLM hallucinations.
   - **Drafted SAR Report**: View the FinCEN regulatory narrative draft.
   - **Investigator Override**: Test submitting a human compliance sign-off override.
4. **Audit Trail**: Inspect the cryptographic **SHA-256 immutable logs** recorded for each agent action.
5. **Model Evaluation**: View live precision, recall ($100\%$), ROC-AUC ($0.9917$), and empirical confusion matrix.

---

## 🐳 Alternative Run Option: Docker Compose

If you have Docker and prefer a single containerized command:

```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend Docs: `http://localhost:8000/docs`

---

## Key Capabilities & Razorpay Track Mapping

| Razorpay Track Requirement | SentinelGraph Implementation | Key Architectural Highlight |
|---|---|---|
| **1. Multi-Agent Reasoning & Orchestration** | LangGraph StateGraph (`backend/app/agents/workflow.py`) | 12 distinct functional nodes orchestrated by a **Supervisor Agent** with **conditional loop-back edges** (max 2 iterations) when forensic uncertainty warrants deeper evidence gathering. |
| **2. Triage & Dual Monitoring** | Phase 1 Engine (`backend/app/services/monitor.py`, `triage.py`) | Dual rule heuristics + scikit-learn `IsolationForest` multidimensional anomaly detection with composite priority ranking. |
| **3. Forensic Planning & Competing Hypotheses** | Planners & Hypotheses (`backend/app/agents/planner.py`, `hypothesis.py`) | Supports both **Static Checklist** (default SOP) and **Adaptive Planner** (LLM-driven re-planning), generating 2–4 competing hypotheses with probabilistic tracking. |
| **4. Deep Forensic Sub-Agents** | 6 Specialized Subagents (`backend/app/agents/subagents/`) | Evidence Retrieval, NetworkX 2-Hop Graph Traversal, Behavioral Baseline Z-Scores, KYC Document Parsing, Mocked PEP/Sanctions Watchlists, and Unified Case Assembly. |
| **5. Deterministic Governance & Compliance** | Risk Assignment & Auditing (`backend/app/agents/risk_scoring.py`, `auditing.py`) | **100% Deterministic Python Risk Scoring** (0–100 score, Low/Med/High/Critical bands, Allow/Review/Block policy). Zero LLM hallucinations. SHA-256 cryptographic audit trails. |
| **6. Regulatory SAR Drafting & Feedback Loop** | SAR Drafter & Feedback (`backend/app/agents/report_drafter.py`, `api/investigations.py`) | FinCEN/FIU-style markdown SAR drafts labeled for compliance officer sign-off, plus interactive human investigator override feedback for continuous policy tuning. |

---

## Empirical Benchmark Evaluation (Held-Out Test Set)

Evaluated via `python backend/run_eval.py` against the synthetic financial test split (**Zero Fabricated Numbers**):

| Metric | Score | Empirical Context |
|---|---|---|
| **Fraud Recall** | **100.00%** | 36 / 36 injected fraud topologies caught (Zero false negatives) |
| **ROC-AUC** | **0.9917** | Outstanding discriminative separation between benign and illicit patterns |
| **Accuracy** | **80.08%** | Total test classification accuracy across all transaction topologies |
| **Triage Precision** | **41.38%** | High-sensitivity surveillance funnel before multi-agent investigation filtering |
| **F1 Score** | **0.5854** | Harmonic balance between aggressive threat detection and operational queue size |

### Confusion Matrix (Test Split $N=256$):
$$\begin{pmatrix} \text{True Positives: } 36 & \text{False Positives: } 51 \\ \text{False Negatives: } 0 & \text{True Negatives: } 169 \end{pmatrix}$$

---

## Deterministic Risk Scoring & Policy Decision Engine

SentinelGraph removes LLM hallucination risk by delegating the final score and policy action to a deterministic mathematical formula combining weighted forensic feature vectors:

$$Score = 100 \times \min\left(1.0, \, 0.25 \cdot \frac{S_{\text{raw}}}{100} + 0.25 \cdot \frac{S_{\text{graph}}}{100} + 0.20 \cdot \frac{S_{\text{behavior}}}{100} + 0.20 \cdot \frac{S_{\text{intel}}}{100} + 0.10 \cdot \frac{S_{\text{doc}}}{100}\right)$$

```
  0 ─── [LOW] ─── 30 ────── [MEDIUM] ────── 60 ────── [HIGH] ────── 80 ── [CRITICAL] ── 100
  ├───── ALLOW ─────┤├────────────── REVIEW ──────────────┤├──────────── BLOCK ────────────┤
```

---

## Repository Structure

```
sentinelgraph-ai/
├── .vscode/                         # Native VS Code Tasks & Launch Configs
│   ├── tasks.json                   # Press Ctrl+Shift+B to start all services
│   └── launch.json                  # Native FastAPI Debugger configuration
├── run_backend.bat                  # 1-Click Windows Backend Launcher
├── run_frontend.bat                 # 1-Click Windows Frontend Launcher
├── run_backend.sh                   # 1-Click macOS/Linux Backend Launcher
├── run_frontend.sh                  # 1-Click macOS/Linux Frontend Launcher
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint with CORS & lifespan
│   │   ├── config.py                # Settings, Groq config, DB URLs, Thresholds
│   │   ├── db/                      # SQLAlchemy models & session management
│   │   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── services/                # Data generator, Monitor, Triage, LLM, GraphStore
│   │   ├── agents/                  # LangGraph Supervisor, Planner, Hypotheses, Subagents, Reasoning, Risk Scoring, Audit, SAR Drafter
│   │   └── api/                     # REST API routers (Alerts, Investigations, Audit, Evaluation)
│   ├── tests/                       # 14 Pytest unit, integration & E2E smoke tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_eval.py                  # Standalone benchmark evaluation CLI
├── frontend/
│   ├── src/
│   │   ├── components/              # RiskBadge, DecisionBadge, AgentTrailCard, NetworkGraphView, SarReportViewer, FeedbackModal, Layout
│   │   ├── pages/                   # Dashboard, AlertsPage, InvestigationsPage, InvestigationDetailPage, AuditLogPage, EvaluationPage
│   │   ├── api/                     # Axios typed client
│   │   └── types/                   # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/
│   ├── architecture_diagram.png     # Rendered architecture diagram
│   ├── generate_diagram.py          # Diagram generation script
│   └── pipeline_spec.md             # Detailed pipeline documentation
├── docker-compose.yml               # Multi-container orchestration (Postgres, Backend, Frontend)
├── render.yaml                      # Render.com Blueprint configuration
├── .env.example
├── .gitignore
└── README.md
```

---

## License & Attribution

Built for the **Razorpay AI Buildathon 2026 ("AI Risk Manager" track)**. All transaction and entity data simulated synthetically for research and demonstration purposes.
