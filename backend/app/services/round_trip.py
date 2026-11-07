"""
Time-respecting round-trip (circular flow) detection.

The old check asked "is there any loop in the 2-hop graph?" — with ordinary background traffic
almost every account has one, so the flag fired on nearly every case. Real round-tripping is
money leaving an account and coming back *in time order* within a short period:

    A --t1--> B --t2--> C --t3--> A     with t1 < t2 < t3 and t3 - t1 <= max_span

Self-transfers (sender == receiver, e.g. a cash deposit into one's own account) are ignored.
"""
import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import Transaction

MAX_HOPS = 4
MAX_SPAN = datetime.timedelta(hours=72)


def find_round_trip(
    db: Session,
    account_id: str,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    max_hops: int = MAX_HOPS,
    max_span: datetime.timedelta = MAX_SPAN,
) -> Optional[List[str]]:
    """Return the txn IDs of the first time-ordered cycle back to `account_id`, or None."""
    q = db.query(Transaction).filter(
        Transaction.sender_account_id == account_id,
        Transaction.receiver_account_id != account_id,
    )
    if start:
        q = q.filter(Transaction.timestamp >= start)
    if end:
        q = q.filter(Transaction.timestamp <= end)

    for first in q.order_by(Transaction.timestamp.asc()).limit(200).all():
        deadline = first.timestamp + max_span
        # Depth-first search over strictly later transactions.
        stack = [(first.receiver_account_id, first.timestamp, [first])]
        while stack:
            node, t_prev, path = stack.pop()
            if len(path) >= max_hops:
                continue
            nxt = db.query(Transaction).filter(
                Transaction.sender_account_id == node,
                Transaction.receiver_account_id != node,
                Transaction.timestamp > t_prev,
                Transaction.timestamp <= deadline,
            ).order_by(Transaction.timestamp.asc()).limit(25).all()
            for t in nxt:
                if t.receiver_account_id == account_id:
                    return [p.txn_id for p in path] + [t.txn_id]
                if t.receiver_account_id in {p.sender_account_id for p in path}:
                    continue  # avoid revisiting accounts already on this path
                stack.append((t.receiver_account_id, t.timestamp, path + [t]))
    return None
