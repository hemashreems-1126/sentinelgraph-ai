import random
import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.db.models import (
    Account, Alert, AuditLog, Customer, EvidenceItem, Hypothesis, InvestigationCase,
    InvestigatorFeedback, Transaction,
)


FIRST_NAMES = ["Alexander", "Elena", "Marcus", "Sophia", "Liam", "Amira", "Carlos", "Priya", "Dmitri", "Fatima",
               "David", "Chen", "Olivia", "Kwame", "Isabella", "Jin", "Ananya", "Lucas", "Amina", "Vikram",
               "Hannah", "Tariq", "Chloe", "Mateo", "Zara", "Rohan", "Svetlana", "Gabriel", "Mei", "Kofi",
               "Noah", "Emma", "Oliver", "Ava", "Elijah", "Charlotte", "William", "Mia", "James", "Harper"]

LAST_NAMES = ["Vance", "Kovacs", "Sterling", "Al-Mansoor", "Dubois", "Patel", "Novak", "Takahashi", "Osei", "Santos",
              "Chen", "Petrov", "Moreau", "Gupta", "Lindqvist", "Zhang", "Nascimento", "Kim", "Larsson", "Sharma",
              "Mercer", "Haddad", "Kowalski", "Bauer", "Ivanov", "Castillo", "Singh", "Fischer", "Popov", "Diallo",
              "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

OCCUPATIONS = [
    "Software Consultant", "Import/Export Merchant", "Real Estate Broker", "Jewelry Dealer",
    "Digital Marketing Agency", "Logistics Coordinator", "Freelance Developer", "Art Trader",
    "Restaurant Owner", "Cryptocurrency Broker", "Construction Contractor", "Healthcare Practitioner",
    "Wholesale Electronics Dealer", "E-commerce Merchant", "Asset Management Advisor", "Financial Broker"
]

KYC_NOTES_TEMPLATES = [
    "Verified passport and utility bill. Customer declared primary source of funds as business revenue.",
    "Enhanced Due Diligence completed. Operates wholesale import/export firm with regular cross-border suppliers.",
    "Standard onboarding. No prior SAR filings on record. Address confirmed via bank statement.",
    "Customer provided corporate registration docs. Sole proprietorship established in 2021.",
    "Customer flagged during periodic review for sudden turnover increase; updated tax returns requested."
]


class SyntheticAMLDataGenerator:
    """
    Synthetic Financial Data Generator for AML / Financial Crime Investigations.
    Produces realistic baseline financial traffic and injects explicit, documented fraud topologies:
    All amounts are INR.
    1. Structuring (Smurfing): repeated cash deposits just under ₹50,000 (PAN-quoting threshold)
    2. Layering: Rapid multi-hop transfers across multiple intermediary shell accounts
    3. Mule Accounts: Dormant/low-activity accounts receiving sudden spikes and immediately draining
    4. Velocity Abuse: High-frequency transaction bursts within minutes
    5. Fan-In Aggregation: Multiple feeder accounts routing funds to single recipient
    6. Fan-Out Dispersion: Single source disbursing funds to multiple recipients
    7. Cycle Loops: Circular wash transactions returning to originator
    8. UPI Mule Chain: many unrelated small UPI credits, then rapid drain to onward accounts
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_and_seed_database(
        self,
        db: Session,
        num_customers: int = 1000,
        num_transactions: int = 15400,
        fraud_ratio: float = 0.12
    ) -> Dict[str, Any]:
        random.seed(self.seed)

        # A new synthetic ledger is a new world: investigations would point at transactions that no
        # longer exist. Clear everything in foreign-key-safe order (children first) — PostgreSQL
        # enforces these links even though SQLite does not.
        for model in (InvestigatorFeedback, AuditLog, Hypothesis, EvidenceItem, InvestigationCase,
                      Alert, Transaction, Account, Customer):
            db.query(model).delete()
        db.commit()

        customers = []
        accounts = []
        transactions = []

        now = datetime.datetime.utcnow()

        # 1. Create Customers
        for i in range(1, num_customers + 1):
            cust_id = f"CUST_{i:04d}"
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}{i}@example-fintech.com"
            occ = random.choice(OCCUPATIONS)
            is_pep = random.random() < 0.03
            is_sanctioned = random.random() < 0.015
            risk_tier = "HIGH" if (is_pep or is_sanctioned) else random.choices(["LOW", "MEDIUM", "HIGH"], weights=[0.65, 0.25, 0.10])[0]

            cust = Customer(
                customer_id=cust_id,
                full_name=name,
                email=email,
                risk_tier=risk_tier,
                kyc_status="VERIFIED",
                occupation=occ,
                country="IN" if random.random() < 0.85 else random.choice(["AE", "SG", "GB", "US"]),
                is_pep=is_pep,
                is_sanctioned=is_sanctioned,
                kyc_notes=random.choice(KYC_NOTES_TEMPLATES),
                # ~8% of genuine customers are also new, so "new account" alone is not proof of fraud.
                created_at=now - datetime.timedelta(
                    days=random.randint(10, 80) if random.random() < 0.08 else random.randint(60, 730)
                )
            )
            customers.append(cust)

            # Each customer has 1 to 2 accounts
            num_accs = 2 if random.random() < 0.3 else 1
            for j in range(1, num_accs + 1):
                acc_id = f"ACC_{cust_id}_{j}"
                acc = Account(
                    account_id=acc_id,
                    customer_id=cust_id,
                    account_type="BUSINESS" if "Merchant" in occ or "Agency" in occ or "Dealer" in occ else "CHECKING",
                    balance=random.uniform(5000, 250000),
                    currency="INR",
                    opened_at=cust.created_at,
                    status="ACTIVE"
                )
                accounts.append(acc)

        db.bulk_save_objects(customers)
        db.bulk_save_objects(accounts)
        db.commit()

        account_ids = [a.account_id for a in accounts]
        opened_map = {a.account_id: a.opened_at for a in accounts}
        target_fraud_txns = int(num_transactions * fraud_ratio)
        normal_txns_count = num_transactions - target_fraud_txns

        # 2. Generate Normal Background Transactions
        for t_idx in range(1, normal_txns_count + 1):
            s_acc, r_acc = random.sample(account_ids, 2)
            # INR amounts: median ~₹1,800, long tail up to ₹2 lakh (legitimate large payments exist)
            amount = round(random.lognormvariate(7.5, 1.3), 2)
            amount = max(10.0, min(amount, 200000.0))
            txn_time = now - datetime.timedelta(days=random.randint(1, 60), minutes=random.randint(0, 1440))
            earliest = max(opened_map[s_acc], opened_map[r_acc])
            if txn_time < earliest:  # an account cannot transact before it is opened
                txn_time = earliest + (now - earliest) * random.random()
            txn_type = random.choice(["UPI", "UPI", "UPI", "IMPS", "NEFT", "CARD", "CASH_DEPOSIT"])

            txn = Transaction(
                txn_id=f"TXN_NORM_{t_idx:06d}",
                sender_account_id=s_acc,
                receiver_account_id=r_acc,
                amount=amount,
                currency="INR",
                txn_type=txn_type,
                channel="BRANCH" if txn_type == "CASH_DEPOSIT" else random.choice(["MOBILE_APP", "ONLINE", "API"]),
                timestamp=txn_time,
                is_fraud_injected=False,
                fraud_pattern_type="NONE"
            )
            transactions.append(txn)

        # 3. Inject Explicit Fraud Topologies
        # `roles` records which accounts the synthetic criminal network controls. It is the
        # evaluation ground truth only — victims and smurf/feeder accounts are ordinary customers.
        roles: Dict[str, str] = {}
        fraud_id_counter = 1
        
        # Topology A: Structuring (Smurfing) — India: repeated cash deposits just under
        # ₹50,000, the amount above which a PAN must be quoted for a cash deposit (Rule 114B).
        num_structuring_groups = max(1, target_fraud_txns // 40)
        for g in range(num_structuring_groups):
            target_acc = random.choice(account_ids)
            roles.setdefault(target_acc, 'STRUCTURING_TARGET')
            feeder_accs = random.sample([a for a in account_ids if a != target_acc], min(6, len(account_ids)-1))
            base_time = now - datetime.timedelta(days=random.randint(1, 14))
            for f_acc in feeder_accs:
                struct_amt = round(random.uniform(45000.0, 49900.0), 2)
                base_time += datetime.timedelta(minutes=random.randint(15, 90))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=f_acc,
                    receiver_account_id=target_acc,
                    amount=struct_amt,
                    currency="INR",
                    txn_type="CASH_DEPOSIT",
                    channel="BRANCH",
                    timestamp=base_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="STRUCTURING"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology B: Layering
        num_layering_chains = max(1, target_fraud_txns // 45)
        for c in range(num_layering_chains):
            chain_length = 5
            chain_accs = random.sample(account_ids, chain_length)
            for _a in chain_accs: roles.setdefault(_a, 'LAYERING_HOP')
            layer_amt = round(random.uniform(50000.0, 150000.0), 2)
            chain_time = now - datetime.timedelta(days=random.randint(1, 20))
            for hop in range(chain_length - 1):
                chain_time += datetime.timedelta(minutes=random.randint(5, 25))
                hop_amt = round(layer_amt * (0.98 ** hop), 2)
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=chain_accs[hop],
                    receiver_account_id=chain_accs[hop + 1],
                    amount=hop_amt,
                    currency="INR",
                    txn_type="WIRE",
                    channel="ONLINE",
                    timestamp=chain_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="LAYERING"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology C: Mule Accounts
        num_mules = max(1, target_fraud_txns // 40)
        for m in range(num_mules):
            mule_acc = random.choice(account_ids)
            roles.setdefault(mule_acc, 'MULE_ACCOUNT')
            source_acc, drain_acc = random.sample([a for a in account_ids if a != mule_acc], 2)
            mule_time = now - datetime.timedelta(days=random.randint(1, 10))
            mule_amt = round(random.uniform(35000.0, 95000.0), 2)
            
            txn1 = Transaction(
                txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                sender_account_id=source_acc,
                receiver_account_id=mule_acc,
                amount=mule_amt,
                currency="INR",
                txn_type="WIRE",
                channel="ONLINE",
                timestamp=mule_time,
                is_fraud_injected=True,
                fraud_pattern_type="MULE_ACCOUNT"
            )
            transactions.append(txn1)
            fraud_id_counter += 1

            txn2 = Transaction(
                txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                sender_account_id=mule_acc,
                receiver_account_id=drain_acc,
                amount=round(mule_amt * 0.97, 2),
                currency="INR",
                txn_type="WIRE",
                channel="ONLINE",
                timestamp=mule_time + datetime.timedelta(minutes=random.randint(10, 45)),
                is_fraud_injected=True,
                fraud_pattern_type="MULE_ACCOUNT"
            )
            transactions.append(txn2)
            fraud_id_counter += 1

        # Topology D: Velocity Abuse
        num_velocity_bursts = max(1, target_fraud_txns // 40)
        for v in range(num_velocity_bursts):
            v_sender, v_receiver = random.sample(account_ids, 2)
            roles.setdefault(v_sender, 'VELOCITY_SOURCE')
            v_time = now - datetime.timedelta(days=random.randint(1, 7))
            for burst in range(10):
                v_time += datetime.timedelta(seconds=random.randint(15, 60))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=v_sender,
                    receiver_account_id=v_receiver,
                    amount=round(random.uniform(1800.0, 5500.0), 2),
                    currency="INR",
                    txn_type="CARD" if random.random() < 0.5 else "WIRE",
                    channel="API",
                    timestamp=v_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="VELOCITY_ABUSE"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology E: Fan-In Aggregation
        num_fanins = max(1, target_fraud_txns // 50)
        for fi in range(num_fanins):
            collector_acc = random.choice(account_ids)
            roles.setdefault(collector_acc, 'FAN_IN_COLLECTOR')
            feeders = random.sample([a for a in account_ids if a != collector_acc], 8)
            fi_time = now - datetime.timedelta(days=random.randint(1, 12))
            for f_acc in feeders:
                fi_time += datetime.timedelta(minutes=random.randint(10, 30))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=f_acc,
                    receiver_account_id=collector_acc,
                    amount=round(random.uniform(8000.0, 14000.0), 2),
                    currency="INR",
                    txn_type="WIRE",
                    channel="ONLINE",
                    timestamp=fi_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="FAN_IN_AGGREGATION"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology F: Fan-Out Dispersion
        num_fanouts = max(1, target_fraud_txns // 50)
        for fo in range(num_fanouts):
            disperser_acc = random.choice(account_ids)
            roles.setdefault(disperser_acc, 'FAN_OUT_DISPERSER')
            recipients = random.sample([a for a in account_ids if a != disperser_acc], 8)
            fo_time = now - datetime.timedelta(days=random.randint(1, 15))
            for r_acc in recipients:
                fo_time += datetime.timedelta(minutes=random.randint(5, 20))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=disperser_acc,
                    receiver_account_id=r_acc,
                    amount=round(random.uniform(4500.0, 9200.0), 2),
                    currency="INR",
                    txn_type="WIRE",
                    channel="ONLINE",
                    timestamp=fo_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="FAN_OUT_DISPERSION"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology G: Cycle Loops
        num_cycles = max(1, target_fraud_txns // 60)
        for cy in range(num_cycles):
            cycle_nodes = random.sample(account_ids, 4)
            for _a in cycle_nodes: roles.setdefault(_a, 'CYCLE_NODE')
            cy_time = now - datetime.timedelta(days=random.randint(1, 18))
            cy_amt = round(random.uniform(40000.0, 80000.0), 2)
            for idx in range(len(cycle_nodes)):
                cy_time += datetime.timedelta(minutes=random.randint(10, 30))
                sender = cycle_nodes[idx]
                receiver = cycle_nodes[(idx + 1) % len(cycle_nodes)]
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=sender,
                    receiver_account_id=receiver,
                    amount=round(cy_amt * (0.99 ** idx), 2),
                    currency="INR",
                    txn_type="WIRE",
                    channel="ONLINE",
                    timestamp=cy_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="CYCLE_TOPOLOGY"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology H: UPI Mule Chain (India) — many unrelated victims pay small UPI amounts
        # into one mule account, which drains ~95% to 2–3 onward accounts within minutes.
        num_upi_mules = max(1, target_fraud_txns // 45)
        for um in range(num_upi_mules):
            mule_acc = random.choice(account_ids)
            others = [a for a in account_ids if a != mule_acc]
            victims = random.sample(others, min(random.randint(6, 10), len(others)))
            onward = random.sample([a for a in others if a not in victims], 2)
            roles.setdefault(mule_acc, 'UPI_MULE')
            for _a in onward: roles.setdefault(_a, 'UPI_ONWARD_MULE')
            um_time = now - datetime.timedelta(days=random.randint(1, 10))
            collected = 0.0
            for v_acc in victims:
                um_time += datetime.timedelta(minutes=random.randint(3, 40))
                amt = round(random.uniform(2000.0, 25000.0), 2)
                collected += amt
                transactions.append(Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=v_acc,
                    receiver_account_id=mule_acc,
                    amount=amt,
                    currency="INR",
                    txn_type="UPI",
                    channel="MOBILE_APP",
                    timestamp=um_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="UPI_MULE_CHAIN"
                ))
                fraud_id_counter += 1
            drain_total = collected * 0.95
            for k, o_acc in enumerate(onward):
                um_time += datetime.timedelta(minutes=random.randint(2, 15))
                transactions.append(Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:06d}",
                    sender_account_id=mule_acc,
                    receiver_account_id=o_acc,
                    amount=round(drain_total / len(onward), 2),
                    currency="INR",
                    txn_type="IMPS",
                    channel="MOBILE_APP",
                    timestamp=um_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="UPI_MULE_CHAIN"
                ))
                fraud_id_counter += 1

        # 4. Hard negatives — LEGITIMATE activity that looks like fraud. Without these, any rule
        #    would look perfect on synthetic data. Labelled benign (is_fraud_injected=False).
        lookalike_counter = 1
        controlled = set(roles)
        benign_pool = [a for a in account_ids if a not in controlled]

        def benign_txn(s, r, amt, ttype, ts, kind):
            nonlocal lookalike_counter
            transactions.append(Transaction(
                txn_id=f"TXN_NORM_L{lookalike_counter:05d}",
                sender_account_id=s, receiver_account_id=r, amount=round(amt, 2), currency="INR",
                txn_type=ttype, channel="BRANCH" if ttype == "CASH_DEPOSIT" else "MOBILE_APP",
                timestamp=ts, is_fraud_injected=False, fraud_pattern_type=f"BENIGN_{kind}",
            ))
            lookalike_counter += 1

        acc_type = {a.account_id: a.account_type for a in accounts}
        business_pool = [a for a in benign_pool if acc_type.get(a) == "BUSINESS"] or benign_pool

        n_lookalikes = max(1, target_fraud_txns // 45)
        for _ in range(n_lookalikes):
            # (a) Kirana / small merchant: customers pay by UPI on most days; the supplier is paid the
            #     NEXT day, partially. Recurring, so the shop has a normal history of collections.
            shop = random.choice(business_pool)
            regulars = random.sample([a for a in benign_pool if a != shop], 25)
            supplier = random.choice([a for a in benign_pool if a not in regulars and a != shop])
            for day in sorted(random.sample(range(1, 40), 8)):
                t0 = now - datetime.timedelta(days=day, hours=random.randint(8, 11))
                day_total = 0.0
                for c in random.sample(regulars, random.randint(7, 11)):
                    t0 += datetime.timedelta(minutes=random.randint(10, 60))
                    amt = random.uniform(150.0, 3000.0); day_total += amt
                    benign_txn(c, shop, amt, "UPI", t0, "MERCHANT_COLLECTION")
                benign_txn(shop, supplier, day_total * random.uniform(0.3, 0.6), "NEFT",
                           t0 + datetime.timedelta(hours=random.randint(18, 30)), "MERCHANT_COLLECTION")

            # (b) Payroll: one employer pays 8 employees within an hour (fan-out look-alike).
            employer = random.choice(business_pool)
            t1 = now - datetime.timedelta(days=random.randint(1, 25))
            for e in random.sample([a for a in benign_pool if a != employer], 8):
                t1 += datetime.timedelta(minutes=random.randint(1, 6))
                benign_txn(employer, e, random.uniform(18000.0, 45000.0), "NEFT", t1, "PAYROLL")

            # (c) Rent split: the same flatmates pay one person by UPI every month, who pays the landlord
            #     in full soon after (the closest look-alike to a mule — a good false-positive test).
            payer = random.choice(benign_pool)
            flatmates = random.sample([a for a in benign_pool if a != payer], random.randint(3, 5))
            landlord = random.choice([a for a in benign_pool if a != payer and a not in flatmates])
            first_day = random.randint(1, 25)
            for month in range(2):
                t2 = now - datetime.timedelta(days=first_day + 30 * month)
                pot = 0.0
                for f in flatmates:
                    t2 += datetime.timedelta(minutes=random.randint(5, 90))
                    amt = random.uniform(6000.0, 12000.0); pot += amt
                    benign_txn(f, payer, amt, "UPI", t2, "RENT_SPLIT")
                benign_txn(payer, landlord, pot, "IMPS", t2 + datetime.timedelta(minutes=random.randint(20, 100)), "RENT_SPLIT")

            # (d) Cash-heavy business depositing daily takings, sometimes just under ₹50,000.
            cash_biz = random.choice(business_pool)
            for d in range(4):
                td = now - datetime.timedelta(days=d * random.randint(1, 3) + 1, hours=random.randint(9, 18))
                benign_txn(cash_biz, cash_biz, random.uniform(28000.0, 49800.0), "CASH_DEPOSIT", td, "CASH_BUSINESS")

        # Typology realism: most mule accounts are recently opened. A new account cannot have
        # history before it was opened, so drop its earlier background transactions.
        new_opened: Dict[str, datetime.datetime] = {}
        for acc_id, role in roles.items():
            if role in ("UPI_MULE", "MULE_ACCOUNT", "UPI_ONWARD_MULE") and random.random() < 0.7:
                opened = now - datetime.timedelta(days=random.randint(15, 70))
                own_fraud = [t.timestamp for t in transactions if t.is_fraud_injected
                             and acc_id in (t.sender_account_id, t.receiver_account_id)]
                if own_fraud:
                    opened = min(opened, min(own_fraud) - datetime.timedelta(days=random.randint(3, 20)))
                new_opened[acc_id] = opened
        if new_opened:
            transactions = [
                t for t in transactions
                if t.is_fraud_injected or not any(
                    a in new_opened and t.timestamp < new_opened[a]
                    for a in (t.sender_account_id, t.receiver_account_id)
                )
            ]

        db.bulk_save_objects(transactions)
        for acc_id, role in roles.items():
            update = {"fraud_role": role}
            if acc_id in new_opened:
                update["opened_at"] = new_opened[acc_id]
            db.query(Account).filter(Account.account_id == acc_id).update(update)
        db.commit()

        from app.services.graph_store import financial_graph_store
        financial_graph_store.invalidate()

        total_txns = len(transactions)
        injected_fraud = len([t for t in transactions if t.is_fraud_injected])

        return {
            "num_customers": len(customers),
            "num_accounts": len(accounts),
            "total_transactions": total_txns,
            "injected_fraud_transactions": injected_fraud,
            "fraud_ratio": round(injected_fraud / total_txns, 4),
            "fraud_controlled_accounts": len(roles),
            "seed": self.seed
        }
