import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from compute_metrics import compute_metrics

csv_path = sys.argv[1]
params_path = sys.argv[2]
report_html = sys.argv[3]
top_designs_csv = sys.argv[4]

with open(params_path) as f:
    run_config = json.load(f)

results_dir = Path(run_config.pop("results_dir")).resolve()

run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]

metrics = compute_metrics(csv_path)
overall = metrics["overall"]

flat_params = {}
for group, group_val in run_config.items():
    if isinstance(group_val, dict):
        for k, v in group_val.items():
            flat_params[f"{group}_{k}"] = v
    else:
        flat_params[group] = group_val

def make_row(run_id, sequence_length, metric_dict, flat_params):
    return {
        "run_id": run_id,
        "sequence_length": sequence_length,
        "sequence_count": metric_dict["target_fold_count"],
        "pct_target_fold": metric_dict["pct_target_fold"],
        "pct_target_fold_high_conf": metric_dict["pct_target_fold_high_conf"],
        "mean_probability": metric_dict["mean_probability"],
        "median_probability": metric_dict["median_probability"],
        **flat_params,
    }

rows = [make_row(run_id, "overall", overall, flat_params)]
for length, length_metrics in metrics["per_length"].items():
    rows.append(make_row(run_id, length, length_metrics, flat_params))

experiments_csv = results_dir / "experiments.csv"
new_rows = pd.DataFrame(rows)
if experiments_csv.exists():
    existing = pd.read_csv(experiments_csv)
    combined = pd.concat([existing, new_rows], ignore_index=True)
else:
    combined = new_rows
combined.to_csv(experiments_csv, index=False)

import shutil

artifacts_dir = results_dir / "artifacts" / run_id
artifacts_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(csv_path, artifacts_dir / "classifications.csv")
shutil.copy(report_html, artifacts_dir / "report.html")
shutil.copy(top_designs_csv, artifacts_dir / "top_designs.csv")

print(f"run_id:    {run_id}")
print(f"Artifacts: {artifacts_dir}")
print(f"Logged to: {experiments_csv}")
