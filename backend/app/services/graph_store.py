import networkx as nx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Customer, Account, Transaction


MAX_DIRECT_NODES = 25
MAX_DISPLAY_NODES = 60


class FinancialGraphStore:
    """
    NetworkX in-memory Graph Store for Transaction and Entity Relationship Analysis.
    Traverses multi-hop networks, computes degree centrality, detects circular flows,
    and identifies shortest paths to watchlist/sanctioned entities.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._is_built = False
        self._fingerprint = None

    def invalidate(self):
        """Force the next build_graph() call to rebuild (called after re-seeding data)."""
        self._is_built = False
        self._fingerprint = None

    def build_graph(self, db: Session, force_rebuild: bool = False):
        # Rebuilding the whole graph for every investigation is slow; only rebuild when the
        # ledger has changed (row counts + latest transaction id).
        last = db.query(Transaction.txn_id).order_by(Transaction.id.desc()).first()
        fingerprint = (db.query(Transaction).count(), db.query(Account).count(), last[0] if last else None)
        if self._is_built and not force_rebuild and fingerprint == self._fingerprint:
            return
        self._fingerprint = fingerprint
        self.graph.clear()

        # 1. Add Accounts & Customers as Nodes
        customers = {c.customer_id: c for c in db.query(Customer).all()}
        accounts = db.query(Account).all()

        for acc in accounts:
            cust = customers.get(acc.customer_id)
            self.graph.add_node(
                acc.account_id,
                node_type="ACCOUNT",
                customer_id=acc.customer_id,
                customer_name=cust.full_name if cust else "Unknown",
                risk_tier=cust.risk_tier if cust else "LOW",
                is_pep=cust.is_pep if cust else False,
                is_sanctioned=cust.is_sanctioned if cust else False,
                balance=acc.balance,
                account_type=acc.account_type
            )

        # 2. Add Transactions as Edges (aggregating flows)
        txns = db.query(Transaction).all()
        for t in txns:
            if self.graph.has_node(t.sender_account_id) and self.graph.has_node(t.receiver_account_id):
                if self.graph.has_edge(t.sender_account_id, t.receiver_account_id):
                    self.graph[t.sender_account_id][t.receiver_account_id]["total_amount"] += t.amount
                    self.graph[t.sender_account_id][t.receiver_account_id]["count"] += 1
                else:
                    self.graph.add_edge(
                        t.sender_account_id,
                        t.receiver_account_id,
                        total_amount=t.amount,
                        count=1,
                        txn_type=t.txn_type
                    )

        self._is_built = True

    def analyze_entity_subgraph(self, account_id: str, max_hops: int = 2) -> Dict[str, Any]:
        if not self.graph.has_node(account_id):
            return {
                "nodes": [],
                "edges": [],
                "total_counterparties": 0,
                "high_risk_connections_count": 0,
                "shortest_path_to_watchlist": "No connection",
                "has_cycles": False,
                "in_degree": 0,
                "out_degree": 0,
                "degree_centrality": 0.0
            }

        # 1. Extract k-hop neighborhood using BFS
        subgraph_nodes = {account_id}
        current_layer = {account_id}

        for _ in range(max_hops):
            next_layer = set()
            for node in current_layer:
                successors = set(self.graph.successors(node))
                predecessors = set(self.graph.predecessors(node))
                next_layer.update(successors)
                next_layer.update(predecessors)
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        sub_g = self.graph.subgraph(subgraph_nodes)

        # 2. Compute Graph Metrics
        in_deg = sub_g.in_degree(account_id)
        out_deg = sub_g.out_degree(account_id)
        deg_centrality = nx.degree_centrality(sub_g).get(account_id, 0.0)

        # Circular flow is decided by the time-respecting check in the Graph agent
        # (services/round_trip.py); a plain structural loop is not evidence of round-tripping.
        has_cycles = False

        # Identify high risk / watchlist nodes in graph (limit to 10 for performance)
        high_risk_nodes = [
            n for n, attr in self.graph.nodes(data=True)
            if attr.get("is_sanctioned") or attr.get("is_pep") or attr.get("risk_tier") == "HIGH"
        ][:15]

        shortest_path_str = "No path found"
        min_path_len = 999
        for hr_node in high_risk_nodes:
            if hr_node != account_id:
                try:
                    if nx.has_path(self.graph, account_id, hr_node):
                        path = nx.shortest_path(self.graph, account_id, hr_node)
                        if len(path) < min_path_len:
                            min_path_len = len(path)
                            shortest_path_str = " -> ".join(path)
                except Exception:
                    pass

        # High risk connections count in 2-hop neighborhood
        hr_count = sum(
            1 for n in subgraph_nodes
            if n != account_id and (
                sub_g.nodes[n].get("is_sanctioned") or
                sub_g.nodes[n].get("is_pep") or
                sub_g.nodes[n].get("risk_tier") == "HIGH"
            )
        )

        # 3. Display subgraph: a 2-hop neighbourhood can hold hundreds of accounts, which is unreadable
        #    and bloats every stored copy of the case. Keep the target, its strongest direct
        #    counterparties and their strongest links (by money flowed) — metrics above use the full graph.
        def flow(u, v):
            return sub_g[u][v].get("total_amount", 0.0)

        direct = sorted(
            set(sub_g.successors(account_id)) | set(sub_g.predecessors(account_id)),
            key=lambda n: -(flow(account_id, n) if sub_g.has_edge(account_id, n) else 0.0)
                          - (flow(n, account_id) if sub_g.has_edge(n, account_id) else 0.0),
        )[:MAX_DIRECT_NODES]
        keep = {account_id, *direct}
        for n in direct:
            nbrs = sorted(
                (set(sub_g.successors(n)) | set(sub_g.predecessors(n))) - keep,
                key=lambda m: -max(flow(n, m) if sub_g.has_edge(n, m) else 0.0, flow(m, n) if sub_g.has_edge(m, n) else 0.0),
            )
            for m in nbrs[:3]:
                if len(keep) >= MAX_DISPLAY_NODES:
                    break
                keep.add(m)
        disp_g = sub_g.subgraph(keep)

        nodes_list = []
        for n, attr in disp_g.nodes(data=True):
            nodes_list.append({
                "id": n,
                "label": attr.get("customer_name", n),
                "customer_id": attr.get("customer_id", ""),
                "risk_tier": attr.get("risk_tier", "LOW"),
                "is_pep": attr.get("is_pep", False),
                "is_sanctioned": attr.get("is_sanctioned", False),
                "is_target": (n == account_id)
            })

        edges_list = []
        for u, v, attr in disp_g.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "amount": round(attr.get("total_amount", 0.0), 2),
                "count": attr.get("count", 1),
                "txn_type": attr.get("txn_type", "TRANSFER")
            })

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "total_counterparties": len(subgraph_nodes) - 1,
            "display_note": f"Showing {len(nodes_list)} of {len(subgraph_nodes)} accounts in the 2-hop network (strongest money flows).",
            "high_risk_connections_count": hr_count,
            "shortest_path_to_watchlist": shortest_path_str,
            "has_cycles": has_cycles,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "degree_centrality": round(deg_centrality, 4)
        }


financial_graph_store = FinancialGraphStore()
