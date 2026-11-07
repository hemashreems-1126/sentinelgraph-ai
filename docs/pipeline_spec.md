# SentinelGraph — Pipeline Specification

Each alert passes through the stages below. LLM steps are **optional**: without a `GROQ_API_KEY`
every LLM step falls back to deterministic logic, and **no LLM ever decides a number, a score, a
filing decision or a fact** — those are plain Python.

| # | Stage | File | Kind | What it does |
|---|---|---|---|---|
| 1 | Synthetic India-first ledger | `services/data_generator.py` | Data | INR ledger with 8 laundering typologies (incl. **UPI mule chains** and **cash just under the ₹50,000 PAN threshold**) **plus legitimate look-alikes** (kirana shops, payroll, rent splits, cash businesses). Records which accounts the criminal network controls — evaluation only. |
| 1b | External data loader | `services/external_data.py` | Data | Loads the public IBM AML dataset (Kaggle) so evaluation is not limited to our own generator. |
| 2 | Transaction monitoring | `services/monitor.py` | Rules + ML | Structuring (PAN threshold), velocity, pass-through (mule vs layering decided from structure, **never from labels**), 24-hour fan-in / fan-out, **UPI mule chain**, plus an Isolation Forest. |
| 3 | Triage | `services/triage.py` | Rules | Ranks alerts by severity and customer risk. |
| 4 | Supervisor / planner / hypotheses | `agents/supervisor.py`, `planner.py`, `hypothesis.py` | LangGraph (+ optional LLM) | Static SOP checklist or adaptive plan; competing hypotheses (incl. "tricked mule" vs "complicit mule"). |
| 5 | Evidence sub-agents | `agents/subagents/*` | Deterministic | Ledger retrieval (labels hidden), money-flow graph + **time-ordered round-trip detection**, **behaviour vs the account's own 45-day baseline**, KYC parsing, mock PEP/sanctions screening, case assembly. |
| 6 | Reasoning | `agents/reasoning.py` | LLM / deterministic | Preliminary synthesis; may loop back once for more evidence. |
| 7 | Risk score | `agents/risk_scoring.py` | Deterministic | Weighted 0–100 score and risk band (used for tiering; see evaluation — it is weak on its own). |
| 8 | **Fact sheet** | `agents/fact_sheet.py` | Deterministic | Turns ledger rows into **evidence-linked claims** (each with record IDs + checkable assertions) and **red flags** (first-time payers, pass-through, PAN-threshold cash, split payments, onward layering, dormant/new account, personal-account collection, round trip…). |
| 9 | **Filing decision** | `agents/filing_decision.py` | Deterministic | `FILE_STR` with **Tier 1/2/3**, or `NO_FILE` with a **documented closure memo**. Needs corroborated evidence, not just a score. |
| 10 | Report drafting | `agents/report_drafter.py` | LLM / template | FIU-IND style STR draft or closure memo. The LLM may only re-word claims; evidence and assertions always come from the fact sheet. |
| 11 | **Fact checker** | `agents/fact_checker.py` | Deterministic | Re-computes every claim from the ledger using only its cited records; flags invented numbers, wrong totals, missing records and numbers in free text; scores 5W1H completeness; **blocks analyst approval** while anything is unverified. |
| 12 | Audit | `agents/auditing.py`, `api/audit.py` | Deterministic | **SHA-256 hash chain** over every agent step and every analyst action; `GET /api/audit/verify/{case_id}` re-verifies it. |
| 13 | Human sign-off | `api/investigations.py` | Human | AGREE / DISAGREE / OVERRIDE. `AGREE` is refused (HTTP 409) while claims are unverified. |
| 14 | Evaluation | `utils/evaluation_runner.py`, `run_eval.py` | Deterministic | Staged evaluation on held-out alerts: detection, filing, fact-check robustness (5 corruption types). |

## Data model & migrations

SQLAlchemy models in `app/db/models.py`; schema changes are **Alembic migrations** in
`backend/alembic/versions` and run automatically on startup (`init_db()`), on SQLite and PostgreSQL.
Databases created by the first release (before migrations) are detected and upgraded in place.
