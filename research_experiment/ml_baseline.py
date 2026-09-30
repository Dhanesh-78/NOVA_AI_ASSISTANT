import pandas as pd
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).parent

train_file = BASE_DIR / "test_commands.csv"
test_file = BASE_DIR / "unseen_test_commands.csv"


# ============================================================
# LOAD DATA
# ============================================================

train_df = pd.read_csv(train_file)
test_df = pd.read_csv(test_file)

# Remove accidental/malformed rows
train_df = train_df.dropna(
    subset=["command", "expected_intent"]
)

test_df = test_df.dropna(
    subset=["command", "expected_intent"]
)

X_train = train_df["command"].astype(str)
y_train = train_df["expected_intent"].astype(str)

X_test = test_df["command"].astype(str)
y_test = test_df["expected_intent"].astype(str)


print("=" * 70)
print("NOVA TF-IDF + LOGISTIC REGRESSION BASELINE")
print("=" * 70)

print(f"Training commands : {len(X_train)}")
print(f"Testing commands  : {len(X_test)}")


# ============================================================
# TF-IDF
# ============================================================

vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    sublinear_tf=True
)

X_train_tfidf = vectorizer.fit_transform(X_train)

X_test_tfidf = vectorizer.transform(X_test)


# ============================================================
# LOGISTIC REGRESSION
# ============================================================

model = LogisticRegression(
    max_iter=2000,
    random_state=42
)

model.fit(X_train_tfidf, y_train)


# ============================================================
# PREDICTION
# ============================================================

y_pred = model.predict(X_test_tfidf)


# ============================================================
# OVERALL METRICS
# ============================================================

accuracy = accuracy_score(y_test, y_pred)

precision_macro, recall_macro, f1_macro, _ = (
    precision_recall_fscore_support(
        y_test,
        y_pred,
        average="macro",
        zero_division=0
    )
)

precision_weighted, recall_weighted, f1_weighted, _ = (
    precision_recall_fscore_support(
        y_test,
        y_pred,
        average="weighted",
        zero_division=0
    )
)


# ============================================================
# PRINT OVERALL RESULTS
# ============================================================

print()
print("=" * 70)
print("OVERALL RESULTS")
print("=" * 70)

print(f"Accuracy            : {accuracy * 100:.2f}%")
print(f"Macro Precision     : {precision_macro * 100:.2f}%")
print(f"Macro Recall        : {recall_macro * 100:.2f}%")
print(f"Macro F1-Score      : {f1_macro * 100:.2f}%")
print(f"Weighted Precision  : {precision_weighted * 100:.2f}%")
print(f"Weighted Recall     : {recall_weighted * 100:.2f}%")
print(f"Weighted F1-Score   : {f1_weighted * 100:.2f}%")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print()
print("=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

labels = sorted(
    set(y_test) | set(y_pred)
)

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

cm_df = pd.DataFrame(
    cm,
    index=labels,
    columns=labels
)

cm_df.index.name = "Actual \\ Predicted"

print()
print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(cm_df.to_string())


# ============================================================
# SAVE PREDICTIONS
# ============================================================

results_df = test_df.copy()

results_df["predicted_intent"] = y_pred

results_df["correct"] = (
    results_df["expected_intent"] ==
    results_df["predicted_intent"]
)

results_file = BASE_DIR / "ml_baseline_results.csv"

results_df.to_csv(
    results_file,
    index=False
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

cm_file = BASE_DIR / "ml_baseline_confusion_matrix.csv"

cm_df.to_csv(cm_file)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame({
    "Metric": [
        "Training Commands",
        "Testing Commands",
        "Accuracy",
        "Macro Precision",
        "Macro Recall",
        "Macro F1-Score",
        "Weighted Precision",
        "Weighted Recall",
        "Weighted F1-Score"
    ],

    "Value": [
        len(X_train),
        len(X_test),
        f"{accuracy * 100:.2f}%",
        f"{precision_macro * 100:.2f}%",
        f"{recall_macro * 100:.2f}%",
        f"{f1_macro * 100:.2f}%",
        f"{precision_weighted * 100:.2f}%",
        f"{recall_weighted * 100:.2f}%",
        f"{f1_weighted * 100:.2f}%"
    ]
})

summary_file = BASE_DIR / "ml_baseline_summary.csv"

summary.to_csv(
    summary_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("=" * 70)
print("FILES CREATED")
print("=" * 70)

print(results_file)
print(cm_file)
print(summary_file)

print("=" * 70)