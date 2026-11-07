"""
Loader for the public IBM "Transactions for Anti Money Laundering (AML)" dataset
(Altman et al., NeurIPS 2023 — https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml).

Why: evaluating only on data our own generator produced is circular. This loads a dataset
SentinelGraph did not create, so the same staged evaluation can be run on it.

Expected CSV columns (e.g. HI-Small_Trans.csv):
    Timestamp, From Bank, Account, To Bank, Account.1, Amount Received, Receiving Currency,
    Amount Paid, Payment Currency, Payment Format, Is Laundering

Notes
  * Accounts are identified by bank + account (account numbers repeat across banks).
  * Amounts are converted to INR with fixed, approximate rates so the same thresholds apply.
    India-specific rules (PAN cash threshold, UPI mule chain) rarely fire on this data because it
    has no UPI channel — results on IBM data measure the generic typologies.
  * Ground truth: an account that sends or receives any laundering transaction is "controlled"
    (Account.fraud_role = "IBM_LAUNDERING"). Labels are used only by the evaluation.
"""
import csv
import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.db.models import (
    Account, Alert, AuditLog, Customer, EvidenceItem, Hypothesis, InvestigationCase,
    InvestigatorFeedback, Transaction,
)

# Approximate INR per unit — only used to put all amounts on one scale.
INR_PER_UNIT = {
    "US Dollar": 83.0, "Euro": 90.0, "UK Pound": 105.0, "Yuan": 11.5, "Yen": 0.56, "Rupee": 1.0,
    "Ruble": 0.9, "Canadian Dollar": 61.0, "Australian Dollar": 55.0, "Swiss Franc": 94.0,
    "Shekel": 22.5, "Mexican Peso": 4.9, "Brazil Real": 16.5, "Saudi Riyal": 22.0, "Bitcoin": 5_000_000.0,
}
FORMAT_TO_TYPE = {
    "Cash": "CASH_DEPOSIT", "Wire": "WIRE", "ACH": "NEFT", "Cheque": "CHEQUE",
    "Credit Card": "CARD", "Reinvestment": "INTERNAL", "Bitcoin": "CRYPTO",
}
REQUIRED = ["Timestamp", "From Bank", "Account", "To Bank", "Account.1", "Amount Paid",
            "Payment Currency", "Payment Format", "Is Laundering"]


def _parse_ts(value: str) -> datetime.datetime:
    for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised timestamp: {value!r}")


def load_ibm_aml_csv(db: Session, path: str, max_rows: Optional[int] = 200_000) -> Dict[str, int]:
    """Replace the current ledger with (up to `max_rows` of) an IBM AML CSV file."""
    for model in (InvestigatorFeedback, AuditLog, Hypothesis, EvidenceItem, InvestigationCase,
                  Alert, Transaction, Account, Customer):
        db.query(model).delete()
    db.commit()

    accounts: Dict[str, Optional[str]] = {}
    txns = []
    skipped = 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Not an IBM AML transactions file — missing columns: {missing}")
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            rate = INR_PER_UNIT.get(row["Payment Currency"])
            if rate is None:
                skipped += 1
                continue
            sender = f"IBM_{row['From Bank']}_{row['Account']}"
            receiver = f"IBM_{row['To Bank']}_{row['Account.1']}"
            laundering = row["Is Laundering"].strip() == "1"
            for acc in (sender, receiver):
                if laundering:
                    accounts[acc] = "IBM_LAUNDERING"
                else:
                    accounts.setdefault(acc, None)
            txns.append(Transaction(
                txn_id=f"IBM_TXN_{i:08d}",
                sender_account_id=sender,
                receiver_account_id=receiver,
                amount=round(float(row["Amount Paid"]) * rate, 2),
                currency="INR",
                txn_type=FORMAT_TO_TYPE.get(row["Payment Format"], row["Payment Format"].upper()),
                channel="BANK",
                timestamp=_parse_ts(row["Timestamp"]),
                is_fraud_injected=laundering,
                fraud_pattern_type="IBM_LAUNDERING" if laundering else "NONE",
            ))

    customers, account_rows = [], []
    for n, (acc_id, role) in enumerate(sorted(accounts.items()), start=1):
        cust_id = f"IBMC_{n:07d}"
        customers.append(Customer(
            customer_id=cust_id, full_name=f"IBM account {acc_id[4:]}", email=f"{cust_id.lower()}@example.org",
            risk_tier="MEDIUM", kyc_status="UNKNOWN", occupation="Not provided in dataset", country="NA",
            is_pep=False, is_sanctioned=False, kyc_notes="External dataset: no KYC information available.",
        ))
        account_rows.append(Account(
            account_id=acc_id, customer_id=cust_id, account_type="UNKNOWN", balance=0.0, currency="INR",
            opened_at=None, status="ACTIVE", fraud_role=role,
        ))
    db.bulk_save_objects(customers)
    db.bulk_save_objects(account_rows)
    db.bulk_save_objects(txns)
    db.commit()

    from app.services.graph_store import financial_graph_store
    financial_graph_store.invalidate()
    return {
        "transactions": len(txns),
        "accounts": len(account_rows),
        "laundering_transactions": sum(t.is_fraud_injected for t in txns),
        "laundering_accounts": sum(1 for r in accounts.values() if r),
        "skipped_rows": skipped,
    }
