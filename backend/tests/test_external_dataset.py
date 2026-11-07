import csv
import datetime
import random

import pytest

from app.db.session import SessionLocal, init_db
from app.db.models import Account, Transaction
from app.services.external_data import load_ibm_aml_csv
from app.services.monitor import transaction_monitor
from app.utils.evaluation_runner import evaluation_runner

HEADER = ["Timestamp", "From Bank", "Account", "To Bank", "Account.1", "Amount Received",
          "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering"]


def _write_ibm_style_csv(path):
    """A small file in the exact IBM AML column format: background traffic + laundering patterns."""
    rnd = random.Random(5)
    t0 = datetime.datetime(2022, 9, 1, 0, 0)
    accs = [(f"{rnd.randint(10, 99):03d}", f"80{rnd.randint(10**6, 10**7):X}") for _ in range(120)]
    rows = []

    def add(ts, a, b, amt, cur="US Dollar", fmt="ACH", laund=0):
        rows.append([ts.strftime("%Y/%m/%d %H:%M"), a[0], a[1], b[0], b[1], f"{amt:.2f}", cur, f"{amt:.2f}", cur, fmt, laund])

    for _ in range(1500):
        a, b = rnd.sample(accs, 2)
        add(t0 + datetime.timedelta(minutes=rnd.randint(0, 60 * 24 * 10)), a, b, rnd.lognormvariate(5, 1))
    collector = accs[0]                                   # laundering fan-in
    for f in accs[1:9]:
        add(t0 + datetime.timedelta(days=4, minutes=rnd.randint(0, 600)), f, collector, rnd.uniform(4000, 9000), fmt="Wire", laund=1)
    chain = accs[20:25]                                   # laundering layering chain
    for i in range(4):
        add(t0 + datetime.timedelta(days=6, minutes=20 * i), chain[i], chain[i + 1], 30000 * 0.97 ** i, fmt="Wire", laund=1)
    add(t0, accs[30], accs[31], 10.0, cur="Unknown Coin")  # unsupported currency → skipped
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        w.writerows(rows)


@pytest.fixture(scope="module")
def loaded(tmp_path_factory):
    init_db()
    path = tmp_path_factory.mktemp("ibm") / "ibm_style.csv"
    _write_ibm_style_csv(path)
    db = SessionLocal()
    stats = load_ibm_aml_csv(db, str(path))
    yield db, stats
    db.close()


def test_loader_maps_columns_and_labels(loaded):
    db, stats = loaded
    assert stats["transactions"] == 1512 and stats["skipped_rows"] == 1
    assert stats["laundering_transactions"] == 12
    assert db.query(Account).filter(Account.fraud_role == "IBM_LAUNDERING").count() == stats["laundering_accounts"]
    t = db.query(Transaction).filter(Transaction.is_fraud_injected == True).first()  # noqa: E712
    assert t.currency == "INR" and t.txn_type == "WIRE" and t.amount > 4000 * 80


def test_rejects_files_that_are_not_ibm_format(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n")
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            load_ibm_aml_csv(db, str(bad))
    finally:
        db.close()


def test_full_evaluation_runs_on_external_data(loaded):
    db, _ = loaded
    transaction_monitor.scan_and_generate_alerts(db)
    res = evaluation_runner.run_benchmark_evaluation(db, max_cases=20, dataset_name="ibm-style-fixture")
    assert res["dataset"] == "ibm-style-fixture"
    assert res["filing"]["cases_investigated"] > 0
    assert res["fact_check"]["genuine_reports_ready"] == 1.0
