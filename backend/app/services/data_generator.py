import random
import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.db.models import Customer, Account, Transaction, Alert


FIRST_NAMES = ["Alexander", "Elena", "Marcus", "Sophia", "Liam", "Amira", "Carlos", "Priya", "Dmitri", "Fatima",
               "David", "Chen", "Olivia", "Kwame", "Isabella", "Jin", "Ananya", "Lucas", "Amina", "Vikram",
               "Hannah", "Tariq", "Chloe", "Mateo", "Zara", "Rohan", "Svetlana", "Gabriel", "Mei", "Kofi"]

LAST_NAMES = ["Vance", "Kovacs", "Sterling", "Al-Mansoor", "Dubois", "Patel", "Novak", "Takahashi", "Osei", "Santos",
              "Chen", "Petrov", "Moreau", "Gupta", "Lindqvist", "Zhang", "Nascimento", "Kim", "Larsson", "Sharma",
              "Mercer", "Haddad", "Kowalski", "Bauer", "Ivanov", "Castillo", "Singh", "Fischer", "Popov", "Diallo"]

OCCUPATIONS = [
    "Software Consultant", "Import/Export Merchant", "Real Estate Broker", "Jewelry Dealer",
    "Digital Marketing Agency", "Logistics Coordinator", "Freelance Developer", "Art Trader",
    "Restaurant Owner", "Cryptocurrency Broker", "Construction Contractor", "Healthcare Practitioner"
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
    1. Structuring (Smurfing): Sub-$10,000 cash/wire deposits within short windows
    2. Layering: Rapid multi-hop transfers across multiple intermediary shell accounts
    3. Mule Accounts: Dormant/low-activity accounts receiving sudden spikes and immediately draining
    4. Velocity Abuse: High-frequency transaction bursts within minutes
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_and_seed_database(
        self,
        db: Session,
        num_customers: int = 200,
        num_transactions: int = 1500,
        fraud_ratio: float = 0.12
    ) -> Dict[str, Any]:
        random.seed(self.seed)

        # Clear existing data cleanly if re-seeding
        db.query(Alert).delete()
        db.query(Transaction).delete()
        db.query(Account).delete()
        db.query(Customer).delete()
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
                country=random.choice(["US", "GB", "DE", "SG", "AE", "IN", "CA", "CH"]),
                is_pep=is_pep,
                is_sanctioned=is_sanctioned,
                kyc_notes=random.choice(KYC_NOTES_TEMPLATES),
                created_at=now - datetime.timedelta(days=random.randint(60, 730))
            )
            customers.append(cust)

            # Each customer has 1 to 2 accounts
            num_accs = 2 if random.random() < 0.3 else 1
            for j in range(1, num_accs + 1):
                acc_id = f"ACC_{cust_id}_{j}"
                acc = Account(
                    account_id=acc_id,
                    customer_id=cust_id,
                    account_type="BUSINESS" if "Merchant" in occ or "Agency" in occ else "CHECKING",
                    balance=random.uniform(5000, 150000),
                    currency="USD",
                    opened_at=cust.created_at,
                    status="ACTIVE"
                )
                accounts.append(acc)

        db.bulk_save_objects(customers)
        db.bulk_save_objects(accounts)
        db.commit()

        account_ids = [a.account_id for a in accounts]
        target_fraud_txns = int(num_transactions * fraud_ratio)
        normal_txns_count = num_transactions - target_fraud_txns

        # 2. Generate Normal Background Transactions
        for t_idx in range(1, normal_txns_count + 1):
            s_acc, r_acc = random.sample(account_ids, 2)
            amount = round(random.lognormvariate(5.5, 1.2), 2)  # Log-normal realistic spending
            amount = max(10.0, min(amount, 45000.0))
            txn_time = now - datetime.timedelta(days=random.randint(1, 60), minutes=random.randint(0, 1440))
            
            txn = Transaction(
                txn_id=f"TXN_NORM_{t_idx:05d}",
                sender_account_id=s_acc,
                receiver_account_id=r_acc,
                amount=amount,
                currency="USD",
                txn_type=random.choice(["WIRE", "ACH", "CARD", "INTERNAL"]),
                channel=random.choice(["ONLINE", "BRANCH", "ATM", "API"]),
                timestamp=txn_time,
                is_fraud_injected=False,
                fraud_pattern_type="NONE"
            )
            transactions.append(txn)

        # 3. Inject Explicit Fraud Topologies
        fraud_id_counter = 1
        
        # Topology A: Structuring (Smurfing) - e.g., 4-6 deposits between $9,000 and $9,950
        num_structuring_groups = max(2, target_fraud_txns // 25)
        for g in range(num_structuring_groups):
            target_acc = random.choice(account_ids)
            feeder_accs = random.sample([a for a in account_ids if a != target_acc], min(5, len(account_ids)-1))
            base_time = now - datetime.timedelta(days=random.randint(1, 14))
            for f_acc in feeder_accs:
                struct_amt = round(random.uniform(9100.0, 9950.0), 2)  # Just below $10,000 CTR
                base_time += datetime.timedelta(minutes=random.randint(15, 90))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:05d}",
                    sender_account_id=f_acc,
                    receiver_account_id=target_acc,
                    amount=struct_amt,
                    currency="USD",
                    txn_type="CASH_DEPOSIT" if random.random() < 0.5 else "WIRE",
                    channel=random.choice(["BRANCH", "ONLINE"]),
                    timestamp=base_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="STRUCTURING"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology B: Layering - Multi-hop pass-through chain
        num_layering_chains = max(2, target_fraud_txns // 30)
        for c in range(num_layering_chains):
            chain_length = 4
            chain_accs = random.sample(account_ids, chain_length)
            layer_amt = round(random.uniform(50000.0, 95000.0), 2)
            chain_time = now - datetime.timedelta(days=random.randint(1, 20))
            for hop in range(chain_length - 1):
                chain_time += datetime.timedelta(minutes=random.randint(5, 25))
                # Slight deduction along the hops
                hop_amt = round(layer_amt * (0.98 ** hop), 2)
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:05d}",
                    sender_account_id=chain_accs[hop],
                    receiver_account_id=chain_accs[hop + 1],
                    amount=hop_amt,
                    currency="USD",
                    txn_type="WIRE",
                    channel="ONLINE",
                    timestamp=chain_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="LAYERING"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        # Topology C: Mule Accounts - Dormant account receiving sudden spike and draining
        num_mules = max(2, target_fraud_txns // 25)
        for m in range(num_mules):
            mule_acc = random.choice(account_ids)
            source_acc, drain_acc = random.sample([a for a in account_ids if a != mule_acc], 2)
            mule_time = now - datetime.timedelta(days=random.randint(1, 10))
            mule_amt = round(random.uniform(28000.0, 65000.0), 2)
            
            # Influx
            txn1 = Transaction(
                txn_id=f"TXN_FRAUD_{fraud_id_counter:05d}",
                sender_account_id=source_acc,
                receiver_account_id=mule_acc,
                amount=mule_amt,
                currency="USD",
                txn_type="WIRE",
                channel="ONLINE",
                timestamp=mule_time,
                is_fraud_injected=True,
                fraud_pattern_type="MULE_ACCOUNT"
            )
            transactions.append(txn1)
            fraud_id_counter += 1

            # Rapid outbound drain
            txn2 = Transaction(
                txn_id=f"TXN_FRAUD_{fraud_id_counter:05d}",
                sender_account_id=mule_acc,
                receiver_account_id=drain_acc,
                amount=round(mule_amt * 0.96, 2),
                currency="USD",
                txn_type="WIRE",
                channel="ONLINE",
                timestamp=mule_time + datetime.timedelta(minutes=random.randint(10, 45)),
                is_fraud_injected=True,
                fraud_pattern_type="MULE_ACCOUNT"
            )
            transactions.append(txn2)
            fraud_id_counter += 1

        # Topology D: Velocity Abuse - Rapid fire micro/medium txns within 10-15 minutes
        num_velocity_bursts = max(2, target_fraud_txns // 30)
        for v in range(num_velocity_bursts):
            v_sender, v_receiver = random.sample(account_ids, 2)
            v_time = now - datetime.timedelta(days=random.randint(1, 7))
            for burst in range(8):
                v_time += datetime.timedelta(seconds=random.randint(15, 60))
                txn = Transaction(
                    txn_id=f"TXN_FRAUD_{fraud_id_counter:05d}",
                    sender_account_id=v_sender,
                    receiver_account_id=v_receiver,
                    amount=round(random.uniform(1500.0, 4800.0), 2),
                    currency="USD",
                    txn_type="CARD" if random.random() < 0.5 else "WIRE",
                    channel="API",
                    timestamp=v_time,
                    is_fraud_injected=True,
                    fraud_pattern_type="VELOCITY_ABUSE"
                )
                transactions.append(txn)
                fraud_id_counter += 1

        db.bulk_save_objects(transactions)
        db.commit()

        total_txns = len(transactions)
        injected_fraud = len([t for t in transactions if t.is_fraud_injected])

        return {
            "num_customers": len(customers),
            "num_accounts": len(accounts),
            "total_transactions": total_txns,
            "injected_fraud_transactions": injected_fraud,
            "fraud_ratio": round(injected_fraud / total_txns, 4),
            "seed": self.seed
        }
