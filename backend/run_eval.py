import os
import json
import sys

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal, init_db
from app.utils.evaluation_runner import evaluation_runner


def main():
    print("=" * 70)
    print("  SentinelGraph — Synthetic Financial Crime Evaluation Runner")
    print("=" * 70)
    
    init_db()
    db = SessionLocal()
    try:
        print("[*] Running benchmark evaluation on held-out test split (seed=42)...")
        results = evaluation_runner.run_benchmark_evaluation(db, split_type="TEST", seed=42)
        
        output_file = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
            
        print("\n" + "=" * 50)
        print("  BENCHMARK EVALUATION RESULTS (HELD-OUT TEST SET)")
        print("=" * 50)
        print(f"  Run ID:              {results['run_id']}")
        print(f"  Total Samples:       {results['total_samples']}")
        print(f"  Precision:           {results['precision_score']:.4f} ({results['precision_score']*100:.2f}%)")
        print(f"  Recall:              {results['recall_score']:.4f} ({results['recall_score']*100:.2f}%)")
        print(f"  F1-Score:            {results['f1_score']:.4f}")
        print(f"  Accuracy:            {results['accuracy_score']:.4f} ({results['accuracy_score']*100:.2f}%)")
        print(f"  ROC-AUC:             {results['roc_auc']:.4f}")
        print("-" * 50)
        print("  Confusion Matrix:")
        print(f"    True Positives:   {results['true_positives']}")
        print(f"    False Positives:  {results['false_positives']}")
        print(f"    True Negatives:   {results['true_negatives']}")
        print(f"    False Negatives:  {results['false_negatives']}")
        print("=" * 50)
        print(f"[+] Saved evaluation artifact to: {output_file}\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
