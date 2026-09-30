import pandas as pd
import sys
from pathlib import Path

# Allow Python to find local_commands.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from local_commands import detect_local_command


# Load UNSEEN test dataset
csv_path = Path(__file__).parent / "unseen_test_commands.csv"
df = pd.read_csv(csv_path)

# Run every command through the rule-based detector
results = []

for _, row in df.iterrows():

    command = row["command"]
    expected = row["expected_intent"]

    predicted, query = detect_local_command(command)

    # Normalize local command labels for research evaluation
    label_mapping = {
        "media_pause": "play_pause",
        "media_next": "next_song",
        "media_previous": "previous_song"
    }

    predicted = label_mapping.get(predicted, predicted)

    correct = predicted == expected

    results.append({
        "id": row["id"],
        "command": command,
        "category": row["category"],
        "expected_intent": expected,
        "predicted_intent": predicted,
        "correct": correct
    })


# Create results dataframe
results_df = pd.DataFrame(results)


# Save detailed results
output_path = Path(__file__).parent / "unseen_rule_based_results.csv"
results_df.to_csv(output_path, index=False)


# Calculate accuracy
accuracy = results_df["correct"].mean() * 100

print("=" * 50)
print("NOVA UNSEEN RULE-BASED EVALUATION")
print("=" * 50)

print(f"Total commands : {len(results_df)}")
print(f"Correct        : {results_df['correct'].sum()}")
print(f"Incorrect      : {(~results_df['correct']).sum()}")
print(f"Accuracy       : {accuracy:.2f}%")

print("=" * 50)
print("Results saved to:")
print(output_path)
print("=" * 50)