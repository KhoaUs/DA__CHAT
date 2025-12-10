import json
from typing import List, Set

BENCHMARK_FILE = r"benchmark/benchmark_search_with_pred.json"
METRICS_OUT = r"benchmark/benchmark_search_metrics.json"


def to_set(lst: List[str]) -> Set[str]:
    """Convert list → cleaned set (loại empty)."""
    return {str(x).strip() for x in lst if x and str(x).strip()}


def precision_recall_f1(gold: Set[str], pred: Set[str]):
    """Compute precision / recall / F1 cho 1 test case."""
    if not gold and not pred:
        return 1.0, 1.0, 1.0

    if not pred:
        return 0.0, 0.0, 0.0

    if not gold:
        return 0.0, 1.0, 0.0

    tp = len(gold & pred)
    fp = len(pred - gold)
    fn = len(gold - pred)

    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

    return precision, recall, f1


def main():
    data = json.load(open(BENCHMARK_FILE, "r", encoding="utf-8"))

    results = []

    total_tp = total_fp = total_fn = 0

    print("\n===========================")
    print("📊 HYBRID SEARCH EVALUATION")
    print("===========================\n")

    for item in data:
        item_id = item["id"]
        gold = to_set(item["gold_skus"])
        pred = to_set(item["pred_result"])

        tp = len(gold & pred)
        fp = len(pred - gold)
        fn = len(gold - pred)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        precision, recall, f1 = precision_recall_f1(gold, pred)

        results.append({
            "id": item_id,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "gold_skus": list(gold),
            "pred_skus": list(pred),
            "gold_count": len(gold),
            "pred_count": len(pred),
            "tp": tp,
            "fp": fp,
            "fn": fn
        })

        print(f"[{item_id}]")
        print(f"  gold = {list(gold)}")
        print(f"  pred = {list(pred)}")
        print(f"  TP={tp} FP={fp} FN={fn}")
        print(f"  Precision={precision:.3f}  Recall={recall:.3f}  F1={f1:.3f}")
        print("-----------------------------------------------------")

    # -------- Global metrics ----------
    overall_precision = total_tp / (total_tp + total_fp) if total_tp + total_fp > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if total_tp + total_fn > 0 else 0.0
    overall_f1 = (
        2 * overall_precision * overall_recall / (overall_precision + overall_recall)
        if overall_precision + overall_recall > 0 else 0.0
    )

    print("\n===========================")
    print("📈 OVERALL METRICS (MICRO)")
    print("===========================")
    print(f"Total TP={total_tp}  FP={total_fp}  FN={total_fn}")
    print(f"Precision = {overall_precision:.4f}")
    print(f"Recall    = {overall_recall:.4f}")
    print(f"F1 Score  = {overall_f1:.4f}")
    print("===========================\n")

    # 🔥 SAVE metrics to file
    metrics_output = {
        "cases": results,
        "overall": {
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": overall_precision,
            "recall": overall_recall,
            "f1": overall_f1
        }
    }

    with open(METRICS_OUT, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, ensure_ascii=False, indent=2)

    print(f"📁 Saved metrics to: {METRICS_OUT}")


if __name__ == "__main__":
    main()
