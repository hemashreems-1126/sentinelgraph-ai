import networkx as nx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Customer, Account, Transaction


class FinancialGraphStore:
    """
    NetworkX in-memory Graph Store for Transaction and Entity Relationship Analysis.
    Traverses multi-hop networks, computes degree centrality, detects circular flows,
    and identifies shortest paths to watchlist/sanctioned entities.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._is_built = False

    def build_graph(self, db: Session, force_rebuild: bool = True):
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

        # Fast O(V+E) cycle detection containing target account
        has_cycles = False
        try:
            # Check if there is a cycle reachable from or containing account_id
            cycle = nx.find_cycle(sub_g, source=account_id, orientation="original")
            has_cycles = len(cycle) > 0
        except Exception:
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

        # 3. Format Subgraph for UI Visualization
        nodes_list = []
        for n, attr in sub_g.nodes(data=True):
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
        for u, v, attr in sub_g.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "amount": attr.get("total_amount", 0.0),
                "count": attr.get("count", 1),
                "txn_type": attr.get("txn_type", "TRANSFER")
            })

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "total_counterparties": len(subgraph_nodes) - 1,
            "high_risk_connections_count": hr_count,
            "shortest_path_to_watchlist": shortest_path_str,
            "has_cycles": has_cycles,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "degree_centrality": round(deg_centrality, 4)
        }


financial_graph_store = FinancialGraphStore()
