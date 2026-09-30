import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).parent

original_file = BASE_DIR / "rule_based_results.csv"
unseen_file = BASE_DIR / "unseen_rule_based_results.csv"


# ============================================================
# LOAD RESULTS
# ============================================================

original = pd.read_csv(original_file)
unseen = pd.read_csv(unseen_file)

# Keep only required columns
original = original[
    ["id", "command", "category", "expected_intent", "predicted_intent"]
]

unseen = unseen[
    ["id", "command", "category", "expected_intent", "predicted_intent"]
]

# Combine both datasets
df = pd.concat([original, unseen], ignore_index=True)

# Remove malformed rows if any
df = df.dropna(
    subset=["expected_intent", "predicted_intent"]
)

df["expected_intent"] = df["expected_intent"].astype(str)
df["predicted_intent"] = df["predicted_intent"].astype(str)


# ============================================================
# BASIC EVALUATION
# ============================================================

total = len(df)

correct = (
    df["expected_intent"] ==
    df["predicted_intent"]
).sum()

incorrect = total - correct

accuracy = correct / total


# ============================================================
# INTENT-LEVEL PRECISION / RECALL / F1
# ============================================================

labels = sorted(
    set(df["expected_intent"]) |
    set(df["predicted_intent"])
)

metrics = []

for intent in labels:

    true_positive = (
        (df["expected_intent"] == intent) &
        (df["predicted_intent"] == intent)
    ).sum()

    false_positive = (
        (df["expected_intent"] != intent) &
        (df["predicted_intent"] == intent)
    ).sum()

    false_negative = (
        (df["expected_intent"] == intent) &
        (df["predicted_intent"] != intent)
    ).sum()

    support = (
        df["expected_intent"] == intent
    ).sum()

    if true_positive + false_positive > 0:
        precision = true_positive / (
            true_positive + false_positive
        )
    else:
        precision = 0

    if true_positive + false_negative > 0:
        recall = true_positive / (
            true_positive + false_negative
        )
    else:
        recall = 0

    if precision + recall > 0:
        f1 = 2 * precision * recall / (
            precision + recall
        )
    else:
        f1 = 0

    metrics.append({
        "Intent": intent,
        "Precision": precision,
        "Recall": recall,
        "F1-Score": f1,
        "Support": support
    })


metrics_df = pd.DataFrame(metrics)


# ============================================================
# MACRO / WEIGHTED METRICS
# ============================================================

macro_precision = metrics_df["Precision"].mean()
macro_recall = metrics_df["Recall"].mean()
macro_f1 = metrics_df["F1-Score"].mean()

weighted_precision = (
    (metrics_df["Precision"] * metrics_df["Support"]).sum()
    / metrics_df["Support"].sum()
)

weighted_recall = (
    (metrics_df["Recall"] * metrics_df["Support"]).sum()
    / metrics_df["Support"].sum()
)

weighted_f1 = (
    (metrics_df["F1-Score"] * metrics_df["Support"]).sum()
    / metrics_df["Support"].sum()
)


# ============================================================
# RESEARCH SUMMARY TABLE
# ============================================================

summary = pd.DataFrame({
    "Metric": [
        "Total Commands",
        "Correct Predictions",
        "Incorrect Predictions",
        "Accuracy",
        "Macro Precision",
        "Macro Recall",
        "Macro F1-Score",
        "Weighted Precision",
        "Weighted Recall",
        "Weighted F1-Score"
    ],

    "Value": [
        total,
        correct,
        incorrect,
        f"{accuracy * 100:.2f}%",
        f"{macro_precision * 100:.2f}%",
        f"{macro_recall * 100:.2f}%",
        f"{macro_f1 * 100:.2f}%",
        f"{weighted_precision * 100:.2f}%",
        f"{weighted_recall * 100:.2f}%",
        f"{weighted_f1 * 100:.2f}%"
    ]
})


# ============================================================
# CONFUSION MATRIX
# ============================================================

confusion_matrix = pd.crosstab(
    df["expected_intent"],
    df["predicted_intent"],
    rownames=["Actual"],
    colnames=["Predicted"],
    dropna=False
)

# Ensure every intent appears in both dimensions
confusion_matrix = confusion_matrix.reindex(
    index=labels,
    columns=labels,
    fill_value=0
)


# ============================================================
# SAVE TABLES
# ============================================================

summary_file = BASE_DIR / "research_evaluation_summary.csv"
metrics_file = BASE_DIR / "research_precision_recall_f1.csv"
confusion_file = BASE_DIR / "research_confusion_matrix.csv"

summary.to_csv(summary_file, index=False)
metrics_df.to_csv(metrics_file, index=False)
confusion_matrix.to_csv(confusion_file)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 70)
print("NOVA RESEARCH EVALUATION")
print("=" * 70)

print()
print("OVERALL RESULTS")
print("-" * 70)
print(summary.to_string(index=False))

print()
print("PRECISION / RECALL / F1 BY INTENT")
print("-" * 70)

display_metrics = metrics_df.copy()

display_metrics["Precision"] = (
    display_metrics["Precision"] * 100
).map(lambda x: f"{x:.2f}%")

display_metrics["Recall"] = (
    display_metrics["Recall"] * 100
).map(lambda x: f"{x:.2f}%")

display_metrics["F1-Score"] = (
    display_metrics["F1-Score"] * 100
).map(lambda x: f"{x:.2f}%")

print(display_metrics.to_string(index=False))

print()
print("CONFUSION MATRIX")
print("-" * 70)
print(confusion_matrix.to_string())

print()
print("=" * 70)
print("FILES CREATED")
print("=" * 70)

print(summary_file)
print(metrics_file)
print(confusion_file)

print()