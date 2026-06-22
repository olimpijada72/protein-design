"""Concatenate all top_designs.csv files from results/artifacts into one CSV."""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
artifacts_dir = PROJECT_ROOT / "results" / "artifacts"
all_designs_output_path = PROJECT_ROOT / "results" / "all_designs.csv"
best_designs_output_path = PROJECT_ROOT / "results" / "best_designs.csv"
fasta_best_designs_output_path = PROJECT_ROOT / "results" / "best_designs.fasta"
PROBABILITY_THRESHOLD = 0.98
PROBABILITY_COLUMN = "CATHe_Prediction_Probability"



dfs = []
for csv_path in sorted(artifacts_dir.glob("*/top_designs.csv")):
    df = pd.read_csv(csv_path)
    df.insert(0, "run_id", csv_path.parent.name)
    dfs.append(df)

if not dfs:
    raise FileNotFoundError(f"No top_designs.csv files found under {artifacts_dir}")



df_all = pd.concat(dfs, ignore_index=True)
df_all.drop_duplicates(subset=["Sequence"], inplace=True)
df_all.to_csv(all_designs_output_path, index=False)
print(f"Wrote {len(df_all)} rows from {len(dfs)} runs to {all_designs_output_path}")


df_all.sort_values(by=PROBABILITY_COLUMN, ascending=False, inplace=True)
df_best = df_all[df_all[PROBABILITY_COLUMN] > PROBABILITY_THRESHOLD]
df_best.reset_index(drop=True, inplace=True)
print(f"Filtered to {len(df_best)} best designs with {PROBABILITY_COLUMN} > {PROBABILITY_THRESHOLD}")

df_best.to_csv(best_designs_output_path, index=False)
print(f"Wrote {len(df_best)} rows to {best_designs_output_path}")

with open(fasta_best_designs_output_path, 'w') as f:
    for idx, row in df_best.iterrows():
        f.write(f'>seq_{idx}\n{row["Sequence"]}\n')
print(f"Wrote {len(df_best)} sequences to {fasta_best_designs_output_path}")
