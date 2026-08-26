# SentinelGraph — Architectural Pipeline Specification

SentinelGraph implements an **11-stage multi-agent financial-crime investigation framework**, designed specifically for the **Razorpay AI Buildathon 2026 ("AI Risk Manager" track)**.

---

## 1. Pipeline Stages & Responsibilities

| Stage # | Component Name | Implementation File | Type | Key Responsibility |
|---|---|---|---|---|
| **1** | **Synthetic AML Simulation** | `backend/app/services/data_generator.py` | Data Simulation | Generates baseline transactions and injects 5 explicit fraud topologies (Structuring, Layering, Smurfing, Mules, Velocity Abuse) with fixed random seed (`42`). |
| **2** | **Transaction Monitor & Anomaly Detector** | `backend/app/services/monitor.py` | Heuristics + ML | Runs dual monitoring: deterministic rule heuristics + scikit-learn `IsolationForest` unsupervised multidimensional anomaly detection. |
| **3** | **Alert Triage & Prioritization** | `backend/app/services/triage.py` | Triage Service | Deduplicates alerts across shared entities, normalizes taxonomy, and calculates composite priority ranking based on severity + customer risk tier. |
| **4** | **Supervisor & Memory Layer** | `backend/app/agents/supervisor.py`, `workflow.py` | LangGraph Orchestration | Orchestrates multi-agent routing, tracks execution state via LangGraph `MemorySaver` checkpointer, and evaluates conditional re-investigation loops. |
| **5A** | **Investigation Planner (Static)** | `backend/app/agents/planner.py` | Deterministic SOP | Generates standard mandatory compliance checklist tailored to the alert typology. |
| **5B** | **Investigation Planner (Adaptive)** | `backend/app/agents/planner.py` | LLM Planning (Groq) | Dynamically plans investigation steps based on initial risk signals and previous iteration evidence. |
| **6** | **Hypothesis Generation Agent** | `backend/app/agents/hypothesis.py` | LLM Reasoning (Groq) | Formulates 2–4 competing hypotheses (e.g. Deliberate Structuring vs Legitimate Commercial Revenue) with prior probabilities. |
| **7A** | **Evidence Retrieval Agent** | `backend/app/agents/subagents/evidence.py` | Subagent | Pulls 90-day transaction ledgers, prior alert history, and customer account profiles. |
| **7B** | **Graph Relationship Agent** | `backend/app/agents/subagents/graph.py` | Subagent (NetworkX) | Traverses 2-hop entity networks, calculates degree centrality, detects circular flows, and finds shortest paths to high-risk/watchlist nodes. |
| **7C** | **Behavior Analysis Agent** | `backend/app/agents/subagents/behavior.py` | Subagent (Stats) | Computes rolling baseline deviations: velocity z-scores, amount z-scores, and outbound fund dissipation ratios. |
| **7D** | **Document Analysis Agent** | `backend/app/agents/subagents/document.py` | Subagent (NLP) | Parses unstructured KYC verification notes, source of funds documentation, and customer occupation declarations. |
| **7E** | **External Intelligence Agent** | `backend/app/agents/subagents/intelligence.py` | Subagent (Mocked) | Simulates real-time PEP, OFAC SDN Sanctions, and Adverse Media watchlist screening. Clearly documented as synthetic mock. |
| **7F** | **Case Assembly Agent** | `backend/app/agents/subagents/assembly.py` | Subagent | Consolidates all subagent evidence into a unified structured case file persisted in PostgreSQL (JSONB). |
| **8** | **Analysis & Reasoning Agent** | `backend/app/agents/reasoning.py` | LLM Reasoning (Groq) | Synthesizes assembled evidence against hypotheses, updates hypothesis probabilities, and evaluates uncertainty to trigger loop-back if needed. |
| **9** | **Risk Assignment Agent** | `backend/app/agents/risk_scoring.py` | **100% Deterministic Python** | Calculates final numeric risk score ($0-100$), assigns Risk Band (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and determines Decision Policy (`ALLOW`, `REVIEW`, `BLOCK`). Zero LLM hallucinations. |
| **10** | **Auditing Agent** | `backend/app/agents/auditing.py` | **Deterministic Logger** | Computes cryptographic SHA-256 digests for every agent action, tool call, and decision, maintaining an immutable compliance audit trail. |
| **11** | **Report / SAR Drafting Agent & Feedback** | `backend/app/agents/report_drafter.py` | LLM Drafting + Human Loop | Drafts human-readable Case Report and standard FinCEN SAR narrative marked as draft requiring human sign-off, with interactive investigator override feedback loop. |

---

## 2. Deterministic Risk Assignment Formula

$$Score = 100 \times \min\left(1.0, \, 0.25 \cdot \frac{S_{\text{raw}}}{100} + 0.25 \cdot \frac{S_{\text{graph}}}{100} + 0.20 \cdot \frac{S_{\text{behavior}}}{100} + 0.20 \cdot \frac{S_{\text{intel}}}{100} + 0.10 \cdot \frac{S_{\text{doc}}}{100}\right)$$

### Risk Bands:
- `0 – 30`: **LOW**
- `31 – 60`: **MEDIUM**
- `61 – 80`: **HIGH**
- `81 – 100`: **CRITICAL**

### Decision Policy Calibration:
- `0 – 30`: **ALLOW** (Benign standard behavior)
- `31 – 70`: **REVIEW** (Borderline or suspicious anomaly requiring compliance analyst sign-off)
- `71 – 100`: **BLOCK** (Severe high-risk breach, structuring, or sanctions proximity)
