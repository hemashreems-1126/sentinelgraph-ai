import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    ax.set_facecolor('#0B0F19')
    fig.patch.set_facecolor('#0B0F19')

    # Title
    plt.text(8.0, 9.5, "SentinelGraph — Multi-Agent Financial Crime Investigation Architecture", 
             fontsize=18, fontweight='bold', color='#FFFFFF', ha='center')
    plt.text(8.0, 9.15, "Razorpay AI Buildathon 2026 • AI Risk Manager Track • 11-Stage End-to-End Pipeline", 
             fontsize=11, color='#818CF8', ha='center', fontfamily='monospace')

    # Helper function for drawing boxes
    def draw_box(x, y, w, h, title, subtitle, color, border_color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", 
                                      linewidth=1.5, edgecolor=border_color, facecolor=color)
        ax.add_patch(rect)
        plt.text(x + w/2, y + h*0.62, title, fontsize=9.5, fontweight='bold', color='#FFFFFF', ha='center', va='center')
        plt.text(x + w/2, y + h*0.32, subtitle, fontsize=7.5, color='#94A3B8', ha='center', va='center')

    # Phase 1: Alert Triage
    rect_p1 = patches.FancyBboxPatch((0.5, 6.2), 15.0, 2.3, boxstyle="round,pad=0.15", 
                                     linewidth=1.5, edgecolor='#3B82F6', facecolor='#1E293B', alpha=0.5)
    ax.add_patch(rect_p1)
    plt.text(0.8, 8.2, "PHASE 1: ALERT TRIAGE & NORMALIZATION", fontsize=10.5, fontweight='bold', color='#60A5FA', fontfamily='monospace')

    draw_box(1.0, 6.5, 4.2, 1.4, "1. Synthetic AML Simulation", "5 Fraud Topologies (Seed 42)", '#0F172A', '#38BDF8')
    draw_box(5.9, 6.5, 4.2, 1.4, "2. Anomaly Monitor", "Rule Heuristics + Isolation Forest", '#0F172A', '#38BDF8')
    draw_box(10.8, 6.5, 4.2, 1.4, "3. Alert Prioritization", "Deduplicate, Categorize & Rank", '#0F172A', '#38BDF8')

    # Arrows Phase 1
    ax.annotate('', xy=(5.8, 7.2), xytext=(5.3, 7.2), arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=2))
    ax.annotate('', xy=(10.7, 7.2), xytext=(10.2, 7.2), arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=2))
    ax.annotate('', xy=(12.9, 5.7), xytext=(12.9, 6.4), arrowprops=dict(arrowstyle="->", color='#6366F1', lw=2))

    # Phase 2: Multi-Agent LangGraph
    rect_p2 = patches.FancyBboxPatch((0.5, 3.2), 15.0, 2.7, boxstyle="round,pad=0.15", 
                                     linewidth=1.5, edgecolor='#6366F1', facecolor='#1E1B4B', alpha=0.5)
    ax.add_patch(rect_p2)
    plt.text(0.8, 5.6, "PHASE 2: MULTI-AGENT LANGGRAPH INVESTIGATION & MEMORY", fontsize=10.5, fontweight='bold', color='#818CF8', fontfamily='monospace')

    draw_box(1.0, 3.6, 2.1, 1.6, "Supervisor\n& Memory", "Short/Long State", '#1E1B4B', '#818CF8')
    draw_box(3.5, 4.5, 2.6, 0.7, "Static Planner", "Default Checklist", '#0F172A', '#6366F1')
    draw_box(3.5, 3.6, 2.6, 0.7, "Adaptive Planner", "Dynamic LLM Replan", '#0F172A', '#6366F1')
    draw_box(6.4, 3.6, 2.4, 1.6, "Hypothesis Agent", "2-4 Competing Theories", '#0F172A', '#818CF8')

    # Sub-agents box
    rect_sub = patches.FancyBboxPatch((9.1, 3.5), 6.1, 1.8, boxstyle="round,pad=0.08", 
                                      linewidth=1.2, edgecolor='#818CF8', facecolor='#0F172A')
    ax.add_patch(rect_sub)
    plt.text(12.15, 5.05, "Specialised Sub-Agents & Knowledge Store", fontsize=8.5, fontweight='bold', color='#A5B4FC', ha='center')
    plt.text(12.15, 4.65, "• Evidence Retrieval (Ledger & History)\n• Graph Relationship (NetworkX 2-Hop)\n• Behavior Analysis (Z-Scores & Ratios)\n• Document Analysis (KYC & Notes)\n• External Intel (Mocked PEP/Sanctions)\n• Case Assembly Agent (Consolidation)", 
             fontsize=7.2, color='#CBD5E1', ha='center', va='center')

    # Arrows Phase 2
    ax.annotate('', xy=(3.4, 4.4), xytext=(3.2, 4.4), arrowprops=dict(arrowstyle="->", color='#818CF8', lw=1.5))
    ax.annotate('', xy=(6.3, 4.4), xytext=(6.2, 4.4), arrowprops=dict(arrowstyle="->", color='#818CF8', lw=1.5))
    ax.annotate('', xy=(9.0, 4.4), xytext=(8.9, 4.4), arrowprops=dict(arrowstyle="->", color='#818CF8', lw=1.5))

    # Loop-back arrow
    ax.annotate('Loop-back (Max 2 Iterations)', xy=(2.0, 3.5), xytext=(7.5, 2.8),
                arrowprops=dict(arrowstyle="->", color='#F59E0B', lw=1.5, connectionstyle="arc3,rad=0.2"),
                fontsize=8, color='#FBBF24', fontfamily='monospace', fontweight='bold')

    # Phase 3: Decision, Governance & Outcomes
    rect_p3 = patches.FancyBboxPatch((0.5, 0.4), 15.0, 2.5, boxstyle="round,pad=0.15", 
                                     linewidth=1.5, edgecolor='#10B981', facecolor='#064E3B', alpha=0.4)
    ax.add_patch(rect_p3)
    plt.text(0.8, 2.6, "PHASE 3: DECISION, REASONING, AUDITING & SAR DRAFTING", fontsize=10.5, fontweight='bold', color='#34D399', fontfamily='monospace')

    draw_box(1.0, 0.7, 3.1, 1.5, "8. Reasoning Agent", "Forensic Synthesis & Eval", '#0F172A', '#34D399')
    draw_box(4.5, 0.7, 3.5, 1.5, "9. Risk Assignment", "100% Deterministic Python\n0-100 Score & Policy", '#0F172A', '#10B981')
    draw_box(8.4, 0.7, 3.1, 1.5, "10. Auditing Agent", "Immutable SHA-256 Logs", '#0F172A', '#34D399')
    draw_box(11.9, 0.7, 3.3, 1.5, "11. SAR Drafter & Feedback", "FinCEN Draft + Human Override", '#0F172A', '#10B981')

    # Arrows Phase 3
    ax.annotate('', xy=(4.4, 1.45), xytext=(4.2, 1.45), arrowprops=dict(arrowstyle="->", color='#34D399', lw=2))
    ax.annotate('', xy=(8.3, 1.45), xytext=(8.1, 1.45), arrowprops=dict(arrowstyle="->", color='#34D399', lw=2))
    ax.annotate('', xy=(11.8, 1.45), xytext=(11.6, 1.45), arrowprops=dict(arrowstyle="->", color='#34D399', lw=2))

    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    plt.tight_layout()
    output_png = os.path.join(os.path.dirname(__file__), "architecture_diagram.png")
    plt.savefig(output_png, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated clean architecture diagram image at: {output_png}")

if __name__ == "__main__":
    create_architecture_diagram()
