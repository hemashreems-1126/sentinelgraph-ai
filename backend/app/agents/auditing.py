import json
import time
import hashlib
import datetime
from typing import Dict, Any, List
from app.agents.state import InvestigationState
from app.db.session import SessionLocal
from app.db.models import AuditLog


GENESIS_HASH = "0" * 64


def generate_audit_hash(actor: str, action: str, timestamp_str: str, payload_str: str, prev_hash: str = GENESIS_HASH) -> str:
    """SHA-256 over the entry AND the previous entry's hash, so entries form a chain:
    editing, deleting or reordering any entry breaks every hash after it."""
    raw = f"{prev_hash}::{actor}::{action}::{timestamp_str}::{payload_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def canonical_payload(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def entry_hash(actor: str, action: str, timestamp: datetime.datetime, payload: Any, prev_hash: str) -> str:
    return generate_audit_hash(actor, action, timestamp.isoformat(), canonical_payload(payload), prev_hash)


def verify_chain(logs: List[Any]) -> Dict[str, Any]:
    """Re-compute the chain for one case's audit entries (ordered by insertion)."""
    prev = GENESIS_HASH
    for i, log in enumerate(logs):
        if (log.prev_hash or GENESIS_HASH) != prev:
            return {"valid": False, "entries": len(logs), "broken_at": i,
                    "reason": f"Entry {i} does not link to the entry before it (missing, deleted or reordered)."}
        expected = entry_hash(log.actor, log.action_type, log.timestamp, log.output_payload, prev)
        if expected != log.verification_hash:
            return {"valid": False, "entries": len(logs), "broken_at": i,
                    "reason": f"Entry {i} ({log.action_type}) was modified after it was recorded."}
        prev = log.verification_hash
    return {"valid": True, "entries": len(logs), "head_hash": prev}


def auditing_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    case_id = state.get("case_id")
    alert_id = state.get("alert_id")
    trail = state.get("agent_trail", [])
    now_iso = datetime.datetime.utcnow().isoformat()

    audit_records: List[Dict[str, Any]] = []
    prev_hash = GENESIS_HASH

    for step in trail:
        actor = step.get("agent_name", "UnknownAgent")
        action = step.get("action", "ACTION_TAKEN")
        # Round-trip through JSON so the hashed payload is exactly what the database stores.
        details = json.loads(canonical_payload(step.get("details", {})))
        ts = datetime.datetime.fromisoformat(step.get("timestamp", now_iso))
        v_hash = entry_hash(actor, action, ts, details, prev_hash)

        audit_records.append({
            "case_id": case_id,
            "alert_id": alert_id,
            "actor": actor,
            "action_type": action,
            "description": step.get("summary", ""),
            "input_payload": {"step_name": actor},
            "output_payload": details,
            "execution_time_ms": step.get("duration_ms", 0.0),
            "verification_hash": v_hash,
            "prev_hash": prev_hash,
            "timestamp": ts.isoformat()
        })
        prev_hash = v_hash

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "AuditingAgent (Deterministic Logger)",
        "action": "AUDIT_TRAIL_COMMITTED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Recorded a SHA-256 hash-chained audit trail of {len(audit_records)} entries (tamper-evident: any edit breaks the chain).",
        "details": {"total_audit_records": len(audit_records), "integrity": "SHA256_HASH_CHAIN", "head_hash": prev_hash},
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["audit_logs"] = audit_records
    state["agent_trail"].append(step_record)
    return state
