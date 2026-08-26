import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState
from app.db.session import SessionLocal
from app.db.models import Transaction, Account, Alert


def evidence_retrieval_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    entity_id = alert.get("entity_id", "")
    entity_type = alert.get("entity_type", "ACCOUNT")

    db = SessionLocal()
    try:
        # Find account IDs related to entity
        if entity_type == "ACCOUNT":
            target_acc_ids = [entity_id]
        elif entity_type == "TRANSACTION":
            txn = db.query(Transaction).filter(Transaction.txn_id == entity_id).first()
            target_acc_ids = [txn.sender_account_id, txn.receiver_account_id] if txn else []
        else:
            accs = db.query(Account).filter(Account.customer_id == entity_id).all()
            target_acc_ids = [a.account_id for a in accs]

        # Fetch transaction history
        txns = db.query(Transaction).filter(
            (Transaction.sender_account_id.in_(target_acc_ids)) |
            (Transaction.receiver_account_id.in_(target_acc_ids))
        ).order_by(Transaction.timestamp.desc()).limit(100).all()

        total_inflow = sum(t.amount for t in txns if t.receiver_account_id in target_acc_ids)
        total_outflow = sum(t.amount for t in txns if t.sender_account_id in target_acc_ids)
        prior_alerts_count = db.query(Alert).filter(
            Alert.entity_id.in_(target_acc_ids),
            Alert.alert_id != alert.get("alert_id")
        ).count()

        txns_list = [
            {
                "txn_id": t.txn_id,
                "sender": t.sender_account_id,
                "receiver": t.receiver_account_id,
                "amount": t.amount,
                "type": t.txn_type,
                "channel": t.channel,
                "timestamp": t.timestamp.isoformat(),
                "is_fraud_injected": t.is_fraud_injected,
                "fraud_pattern_type": t.fraud_pattern_type
            }
            for t in txns[:20]
        ]

        evidence_data = {
            "target_account_ids": target_acc_ids,
            "total_transactions_analyzed": len(txns),
            "total_inflow": round(total_inflow, 2),
            "total_outflow": round(total_outflow, 2),
            "net_flow": round(total_inflow - total_outflow, 2),
            "prior_alerts_on_file": prior_alerts_count,
            "recent_transactions": txns_list
        }
    finally:
        db.close()

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "EvidenceRetrievalAgent",
        "action": "EVIDENCE_RETRIEVED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Retrieved {len(txns)} transactions (Inflow: ${total_inflow:,.2f}, Outflow: ${total_outflow:,.2f}) and {prior_alerts_count} historical alerts.",
        "details": evidence_data,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["evidence_data"] = evidence_data
    state["agent_trail"].append(step_record)
    return state
