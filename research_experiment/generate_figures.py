import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).parent
FIGURE_DIR = BASE_DIR / "figures"
FIGURE_DIR.mkdir(exist_ok=True)

# ==========================================
# RESULTS
# ==========================================

rule_accuracy = 100.00
ml_accuracy = 38.60

rule_precision = 100.00
ml_precision = 19.25

rule_recall = 100.00
ml_recall = 25.71

rule_f1 = 100.00
ml_f1 = 21.02

# ==========================================
# FIGURE 1 — ACCURACY COMPARISON
# ==========================================

methods = [
    "Rule-Based NOVA",
    "TF-IDF + Logistic Regression"
]

accuracy = [
    rule_accuracy,
    ml_accuracy
]

plt.figure(figsize=(8, 5))

bars = plt.bar(methods, accuracy)

plt.ylabel("Accuracy (%)")
plt.title("Accuracy Comparison of Intent Detection Methods")
plt.ylim(0, 110)

for bar, value in zip(bars, accuracy):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value + 2,
        f"{value:.2f}%",
        ha="center",
        fontweight="bold"
    )

plt.tight_layout()

plt.savefig(
    FIGURE_DIR / "accuracy_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# FIGURE 2 — PRECISION / RECALL / F1
# ==========================================

metrics = ["Precision", "Recall", "F1-Score"]

rule_scores = [
    rule_precision,
    rule_recall,
    rule_f1
]

ml_scores = [
    ml_precision,
    ml_recall,
    ml_f1
]

x = range(len(metrics))
width = 0.35

plt.figure(figsize=(9, 5))

bars1 = plt.bar(
    [i - width / 2 for i in x],
    rule_scores,
    width,
    label="Rule-Based NOVA"
)

bars2 = plt.bar(
    [i + width / 2 for i in x],
    ml_scores,
    width,
    label="TF-IDF + Logistic Regression"
)

plt.xticks(list(x), metrics)
plt.ylabel("Score (%)")
plt.title("Precision, Recall and F1-Score Comparison")
plt.ylim(0, 110)
plt.legend()

for bars in [bars1, bars2]:
    for bar in bars:
        value = bar.get_height()

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + 2,
            f"{value:.2f}",
            ha="center",
            fontsize=9
        )

plt.tight_layout()

plt.savefig(
    FIGURE_DIR / "precision_recall_f1_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# FIGURE 3 — ML CONFUSION MATRIX
# ==========================================

cm_file = BASE_DIR / "ml_baseline_confusion_matrix.csv"

cm = pd.read_csv(cm_file, index_col=0)

plt.figure(figsize=(16, 13))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    cbar=True,
    linewidths=0.5
)

plt.title(
    "Confusion Matrix — TF-IDF + Logistic Regression",
    fontsize=15
)

plt.xlabel("Predicted Intent")
plt.ylabel("Actual Intent")

plt.xticks(
    rotation=90,
    fontsize=7
)

plt.yticks(
    rotation=0,
    fontsize=7
)

plt.tight_layout()

plt.savefig(
    FIGURE_DIR / "ml_confusion_matrix.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# DONE
# ==========================================

print()
print("=" * 55)
print("RESEARCH FIGURES GENERATED SUCCESSFULLY")
print("=" * 55)

print()
print("Saved files:")

print(FIGURE_DIR / "accuracy_comparison.png")
print(FIGURE_DIR / "precision_recall_f1_comparison.png")
print(FIGURE_DIR / "ml_confusion_matrix.png")

print()
print("All figures saved at 300 DPI.")