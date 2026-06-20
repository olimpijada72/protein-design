"""Concatenate all top_designs.csv files from results/artifacts into one CSV."""

import pandas as pd
from pathlib import Path

artifacts_dir = Path("/Users/mipopovic/Desktop/protein-design/results/artifacts/")
output_path = Path("/Users/mipopovic/Desktop/protein-design/results/all_designs.csv")

dfs = []
for csv_path in sorted(artifacts_dir.glob("*/top_designs.csv")):
    df = pd.read_csv(csv_path)
    df.insert(0, "run_id", csv_path.parent.name)
    dfs.append(df)

if not dfs:
    raise FileNotFoundError(f"No top_designs.csv files found under {artifacts_dir}")

combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(output_path, index=False)
print(f"Wrote {len(combined)} rows from {len(dfs)} runs to {output_path}")
