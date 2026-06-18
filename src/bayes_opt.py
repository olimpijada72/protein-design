"""
Bayesian hyperparameter optimisation targeting pct_target_fold_high_conf.

Each protein length gets its own independent Optuna study so the optimizer
learns a separate landscape per length. After each run the best params are
written to results/best_params_per_length.json for easy comparison.

Usage (from project root):
    python src/bayes_opt.py --nres-lens 95        # optimize for length 95
    python src/bayes_opt.py --nres-lens 150       # optimize for length 150
    python src/bayes_opt.py --nres-lens 250       # optimize for length 250

Optional flags:
    --n-trials 60          number of new trials to run (default: 40)
    --study-name my_study  override the auto-generated study name
    --no-warmup            skip seeding from prior experiments.csv rows
"""

import argparse
import json
import subprocess
from pathlib import Path

import optuna
import pandas as pd

optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT       = Path(__file__).resolve().parent.parent
PIPELINE_DIR       = PROJECT_ROOT / "pipeline"
RESULTS_CSV        = PROJECT_ROOT / "results" / "experiments.csv"
BEST_PARAMS_JSON   = PROJECT_ROOT / "results" / "best_params_per_length.json"

# ── Search space ─────────────────────────────────────────────────────────────
SEARCH_SPACE = {
    "guidance_weight":    (0.5, 4.0),
    "autoguidance_ratio": (0.0, 1.0),
    "caflow_noise_scale": (0.2, 0.6),
    "sampling_temp":      (0.1, 1.0),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def existing_run_ids() -> set[str]:
    if not RESULTS_CSV.exists():
        return set()
    return set(pd.read_csv(RESULTS_CSV)["run_id"].unique())


def read_metric(run_id: str, nres_lens: int) -> float:
    """Read pct_target_fold_high_conf for the specific length row of a run."""
    df = pd.read_csv(RESULTS_CSV)
    # sequence_length is stored as a string (mixed with "overall")
    row = df[(df["run_id"] == run_id) & (df["sequence_length"] == str(nres_lens))]
    if row.empty:
        raise ValueError(
            f"No row for run_id={run_id}, sequence_length={nres_lens} in experiments.csv"
        )
    return float(row["pct_target_fold_high_conf"].iloc[0])


def load_warmup(study: optuna.Study, nres_lens: int) -> None:
    """Seed the study with prior runs for this specific length."""
    if not RESULTS_CSV.exists():
        return

    required = [
        "proteina_guidance_weight",
        "proteina_autoguidance_ratio",
        "proteina_caflow_noise_scale",
        "mpnn_sampling_temp",
        "pct_target_fold_high_conf",
    ]
    df = pd.read_csv(RESULTS_CSV)
    # Keep only rows for this length (exclude "overall" and other lengths)
    df = df[df["sequence_length"] == str(nres_lens)].dropna(subset=required)

    existing_warmup = {
        t.user_attrs["run_id"]
        for t in study.trials
        if "run_id" in t.user_attrs
    }

    distributions = {
        name: optuna.distributions.FloatDistribution(lo, hi)
        for name, (lo, hi) in SEARCH_SPACE.items()
    }

    added = 0
    for _, row in df.iterrows():
        if row["run_id"] in existing_warmup:
            continue
        trial = optuna.trial.create_trial(
            params={
                "guidance_weight":    float(row["proteina_guidance_weight"]),
                "autoguidance_ratio": float(row["proteina_autoguidance_ratio"]),
                "caflow_noise_scale": float(row["proteina_caflow_noise_scale"]),
                "sampling_temp":      float(row["mpnn_sampling_temp"]),
            },
            distributions=distributions,
            value=float(row["pct_target_fold_high_conf"]),
        )
        study.add_trial(trial)
        added += 1

    if added:
        print(f"[warmup] Seeded {added} prior trial(s) for length {nres_lens} from experiments.csv")


def save_best_params(nres_lens: int, study: optuna.Study) -> None:
    """Append/update best params for this length in best_params_per_length.json."""
    best = study.best_trial
    entry = {
        "study_name":                 study.study_name,
        "n_completed_trials":         len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]),
        "best_pct_target_fold_high_conf": best.value,
        "best_run_id":                best.user_attrs.get("run_id", "warmup_trial"),
        "best_params": {k: round(v, 6) for k, v in best.params.items()},
    }

    summary = {}
    if BEST_PARAMS_JSON.exists():
        with open(BEST_PARAMS_JSON) as f:
            summary = json.load(f)

    summary[str(nres_lens)] = entry

    with open(BEST_PARAMS_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[saved] Best params written to {BEST_PARAMS_JSON}")


# ── Objective ────────────────────────────────────────────────────────────────

def make_objective(nres_lens: int):
    def objective(trial: optuna.Trial) -> float:
        params = {
            name: trial.suggest_float(name, lo, hi)
            for name, (lo, hi) in SEARCH_SPACE.items()
        }

        before_ids = existing_run_ids()

        cmd = [
            "nextflow", "run", "main.nf", "-with-conda",
            "--proteina.guidance_weight",    str(params["guidance_weight"]),
            "--proteina.autoguidance_ratio", str(params["autoguidance_ratio"]),
            "--proteina.caflow_noise_scale", str(params["caflow_noise_scale"]),
            "--mpnn.sampling_temp",          str(params["sampling_temp"]),
            "--proteina.nres_lens",          str(nres_lens),
        ]

        print(f"\n[trial {trial.number}] nres_lens={nres_lens}  params={params}")
        proc = subprocess.run(cmd, cwd=PIPELINE_DIR, text=True, capture_output=False)

        if proc.returncode != 0:
            raise RuntimeError(
                f"Nextflow exited with code {proc.returncode} — trial marked FAILED"
            )

        new_ids = existing_run_ids() - before_ids
        if not new_ids:
            raise RuntimeError(
                "Pipeline succeeded but no new run_id appeared in experiments.csv"
            )

        run_id = new_ids.pop()
        trial.set_user_attr("run_id", run_id)

        metric = read_metric(run_id, nres_lens)
        print(f"[trial {trial.number}] run_id={run_id}  pct_target_fold_high_conf={metric:.2f}%")
        return metric

    return objective


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bayesian HPO for protein backbone generation."
    )
    parser.add_argument(
        "--nres-lens", type=int, required=True,
        help="Protein length to optimise for (e.g. 95, 150, 250)"
    )
    parser.add_argument(
        "--n-trials", type=int, default=40,
        help="Number of new trials to run (default: 40)"
    )
    parser.add_argument(
        "--study-name", default=None,
        help="Override auto-generated study name (default: hpo_len<nres_lens>)"
    )
    parser.add_argument(
        "--no-warmup", action="store_true",
        help="Do not seed the study from prior experiments.csv rows"
    )
    args = parser.parse_args()

    study_name = args.study_name or f"hpo_len{args.nres_lens}"
    db_path    = PROJECT_ROOT / "results" / f"optuna_{study_name}.db"

    print(f"Study : {study_name}")
    print(f"Length: {args.nres_lens} residues")
    print(f"Trials: {args.n_trials}")
    print(f"DB    : {db_path}\n")

    study = optuna.create_study(
        direction="maximize",
        storage=f"sqlite:///{db_path}",
        study_name=study_name,
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=42),
    )

    if not args.no_warmup:
        load_warmup(study, args.nres_lens)

    study.optimize(
        make_objective(args.nres_lens),
        n_trials=args.n_trials,
        show_progress_bar=True,
    )

    best = study.best_trial
    print("\n=== Best trial ===")
    print(f"  nres_lens                 : {args.nres_lens}")
    print(f"  pct_target_fold_high_conf : {best.value:.2f}%")
    print(f"  run_id                    : {best.user_attrs.get('run_id', 'N/A (warmup trial)')}")
    print("  Params:")
    for k, v in best.params.items():
        print(f"    {k:25s}: {v:.4f}")

    save_best_params(args.nres_lens, study)

    print(f"\nVisualise: optuna-dashboard sqlite:///{db_path}")


if __name__ == "__main__":
    main()
