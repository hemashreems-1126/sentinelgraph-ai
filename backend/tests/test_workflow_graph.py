from app.agents.workflow import should_loop_back, compiled_investigation_graph
from app.agents.state import InvestigationState


def test_conditional_loop_back_decision():
    # Loop back required when needs_more_evidence is True and iteration < 2
    state_loop: InvestigationState = {
        "needs_more_evidence": True,
        "iteration_count": 1
    }
    assert should_loop_back(state_loop) == "supervisor"

    # Route to risk scoring when iterations reach max or sufficient evidence exists
    state_proceed_1: InvestigationState = {
        "needs_more_evidence": True,
        "iteration_count": 2
    }
    assert should_loop_back(state_proceed_1) == "risk_scoring"

    state_proceed_2: InvestigationState = {
        "needs_more_evidence": False,
        "iteration_count": 1
    }
    assert should_loop_back(state_proceed_2) == "risk_scoring"


def test_compiled_graph_structure():
    assert compiled_investigation_graph is not None
    # Verify graph contains key nodes
    nodes = compiled_investigation_graph.nodes
    assert "supervisor" in nodes
    assert "planner" in nodes
    assert "hypothesis" in nodes
    assert "evidence_retrieval" in nodes
    assert "graph_relationship" in nodes
    assert "behavior_analysis" in nodes
    assert "document_analysis" in nodes
    assert "external_intelligence" in nodes
    assert "case_assembly" in nodes
    assert "reasoning" in nodes
    assert "risk_scoring" in nodes
    assert "auditing" in nodes
    assert "report_drafter" in nodes
