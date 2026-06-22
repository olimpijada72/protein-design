import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
BEST_DESIGNS = ROOT / "results/best_designs.csv"
FOLDSEEK_RESULTS = ROOT / "results/foldseek/foldseek_results.txt"
OUT_TXT = ROOT / "results/best_200_validated_sequences.txt"
OUT_FASTA = ROOT / "results/best_200_validated_sequences.fasta"

foldseek_cols = [
    "query", "target", "fident", "alnlen", "mismatch", "gapopen",
    "qstart", "qend", "tstart", "tend", "evalue", "bits",
]

best = pd.read_csv(BEST_DESIGNS)
best["seq_id"] = [f"seq_{i}" for i in range(len(best))]

fs = pd.read_csv(FOLDSEEK_RESULTS, sep="\t", header=None, names=foldseek_cols)
fs["seq_id"] = fs["query"].str.extract(r"^(seq_\d+)_ptm")
fs["cath_hit"] = fs["target"].str.extract(r"(\d+\.\d+\.\d+\.\d+)$")

merged = fs.merge(best[["seq_id", "CATHe_Predicted_SFAM", "Sequence"]], on="seq_id", how="left")

exact_match = (
    merged.groupby("seq_id")
    .apply(lambda g: (g["cath_hit"] == g["CATHe_Predicted_SFAM"].iloc[0]).any(), include_groups=False)
    .rename("exact_cath_match")
    .reset_index()
)

broad_match = (
    merged.groupby("seq_id")
    .apply(lambda g: g["cath_hit"].str.startswith("2.60.40.", na=False).any(), include_groups=False)
    .rename("has_2_60_40_hit")
    .reset_index()
)

result = best.merge(exact_match, on="seq_id").merge(broad_match, on="seq_id")

print(f"Total sequences:        {len(result)}")
print(f"Exact CATH match:       {result['exact_cath_match'].sum()}")
print(f"Has 2.60.40.x hit:      {result['has_2_60_40_hit'].sum()}")

validated = result[result["has_2_60_40_hit"]].head(200)
sequences = validated["Sequence"]

with open(OUT_TXT, "w") as f:
    f.write("\n".join(sequences))

with open(OUT_FASTA, "w") as f:
    for i, seq in enumerate(sequences):
        f.write(f">seq_{i}\n{seq}\n")

print(f"Saved {len(sequences)} sequences to {OUT_TXT} and {OUT_FASTA}")
