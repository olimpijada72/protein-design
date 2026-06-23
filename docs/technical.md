# Protein Design Pipeline: Technical Reference

> How the pipeline is implemented — processes, configuration, scripts, and data flow.
> For the theoretical background on each model, see `docs/THEORY_EXPLANATION.MD`.

---

## Table of Contents

1. [Data Flow](#1-data-flow)
2. [Proteína — Backbone Generation](#2-proteína--backbone-generation)
3. [ProteinMPNN — Sequence Design](#3-proteinmpnn--sequence-design)
4. [CATHe2 — Fold Classification](#4-cathe2--fold-classification)
5. [Nextflow Pipeline (main.nf)](#5-nextflow-pipeline-mainnf)
6. [Pipeline Configuration (nextflow.config)](#6-pipeline-configuration-nextflowconfig)
7. [Bayesian HPO (bayes_opt.py)](#7-bayesian-hpo-bayes_optpy)
8. [Post-Pipeline Scripts](#8-post-pipeline-scripts)
9. [Artifact Layout](#9-artifact-layout)

---

## 1. Data Flow

```
nextflow.config
      │
      ▼
GENERATE_BACKBONES          → backbones/*.pdb
      │ (flatten: one pdb per item)
      ▼
RUN_MPNN  ×N (parallel)     → seqs/*.fa  (per backbone)
      │ (collect: all fastas)
      ▼
RUN_CATHE                   → classifications.csv
      │
      ├──► GENERATE_REPORT  → top_designs.csv, report.html
      │          │
      └──────────┴──► LOG_RUN → results/artifacts/<run_id>/
                                results/experiments.csv
```

After the Nextflow pipeline, three standalone scripts handle post-processing:

```
concat_designs.py    → results/best_designs.csv, results/best_designs.fasta
      │
      ▼
ESMFold (Colab)      → .pdb files
      │
      ▼
run_foldseek.sh      → results/foldseek/foldseek_results.txt
      │
      ▼
final_validation.py  → results/best_200_validated_sequences.fasta
```

---

## 2. Proteína — Backbone Generation

Flow-matching backbone generator: maps Gaussian noise → CATH-conditioned 3D protein structures.

### Invocation

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples <N> \
    seed=5 \
    dt=0.0025 \
    guidance_weight=1.015415 \
    autoguidance_ratio=0.792596 \
    sampling_caflow.sampling_mode=sc \
    sampling_caflow.sc_scale_noise=0.262678 \
    nres_lens=[95]
```

The pipeline calls Proteína using Hydra config overrides (the `key=value` arguments after the flags). This lets `nextflow.config` control all generative parameters without touching the Proteína source code or YAML files.

### Four Complementary Guidance Signals

| Signal | Controls |
|---|---|
| CATH label | Macro-level fold class (topology level) |
| CFG (`guidance_weight`) | Semantic alignment to target fold |
| Autoguidance (`autoguidance_ratio`) | Physical geometry correction |
| Self-conditioning (`self_cond: True`) | Temporal consistency across timesteps |

Outputs are fold-consistent **and** geometrically realistic before any sequence design occurs.

---

### Key Arguments

#### `--cath_codes 2.60.40.x`

Restricts sampling to the Ig-like β-sandwich fold family via the CATH hierarchy.

| Level | Value | Meaning |
|---|---|---|
| Class | `2` | Mainly β-class proteins |
| Architecture | `60` | β-sandwich-like structures |
| Topology | `40` | Immunoglobulin-like fold family |
| Homology | `x` | Wildcard (any superfamily) |

The `x` wildcard means Proteína samples any superfamily within the 2.60.40 topology — the pipeline intentionally does not over-constrain here.

#### `--config_name inference_cond_autoguidance`

Selects the sampling config that enables CFG + autoguidance correction. Loads `inference_cond_autoguidance.yaml` on top of the base config:

```yaml
# inference_cond_autoguidance.yaml
defaults:
  - inference_base
  - _self_

ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt
autoguidance_ckpt_path: "/path/to/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"
self_cond: True
fold_cond: True
cath_code_level: "T"
guidance_weight: 2.0
sampling_caflow:
  sampling_mode: sc
```

Parameters that appear here can be further overridden by the Nextflow pipeline via Hydra command-line overrides.

<details>
<summary>Full base config — inference_base.yaml</summary>

```yaml
run_name_: "testing_IgFold_2.60.40_Sweep"
ckpt_path: "/path/to/proteina/data/checkpoints"
ckpt_name:

ncpus_: 24
seed: 5

nres_lens: [95, 100, 105, 110, 115]
nsamples_per_len: 2
max_nsamples: 5

dt: 0.0025
self_cond: True

sampling_caflow:
  sampling_mode: sc
  sc_scale_noise: 0.3
  sc_scale_score: 1.0
  gt_mode: "1/t"
  gt_p: 1.0
  gt_clamp_val: null

schedule:
  schedule_mode: log
  schedule_p: 2.0

fold_cond: True
cath_code_level: "T"
len_cath_code_path: ${oc.env:DATA_PATH}/metric_factory/features/D_FS_afdb_cath_codes.pth

guidance_weight: 2.0
autoguidance_ratio: 0.5
autoguidance_ckpt_path: "/path/to/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"

lora:
  use: false
  lora_alpha: 32.0
  lora_dropout: 0.0
  r: 16
  train_bias: "none"

designability_seqs_per_struct: 8
compute_designability: True
compute_fid: False
```

</details>

<details>
<summary>SDE/ODE sampling — math details</summary>

The ODE form: `dx_t = v(x_t, t) dt`

The SDE form: `dx_t = v(x_t, t) dt + g_t · s(x_t, t) dt + √(2g_t) dw_t`

Both produce the same marginal distributions for any `g_t`. Key parameters:

- `sampling_mode: sc` — SDE sampling (vs `vf` for ODE)
- `sc_scale_noise` — scales the `√(2g_t)` noise term
- `sc_scale_score` — scales the `g_t · s(x_t, t)` score term
- `g_t = sc_g · min(5, (1-t)/t)` — from optimal transport coupling

</details>

---

### Key Config Parameters

#### `ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt`

Loads the primary generation model (trained on 21M AlphaFoldDB structures, ~400M parameters, uses triangular multiplicative update layers from AF3).

#### `autoguidance_ckpt_path`

Loads a weaker early-training checkpoint (~10k steps) used as a geometry reference. The vector field difference between the strong and weak checkpoints produces the autoguidance correction signal.

| Component | Role |
|---|---|
| Strong checkpoint (`v1.4`) | Primary generation |
| Weak checkpoint (`v1.8` early) | Geometry correction reference |
| Field difference | Autoguidance correction signal |

#### `self_cond: True`

Feeds the previous timestep's prediction back into the model as an additional input. Reduces per-step noise and improves sampling stability, especially for longer chains.

#### `fold_cond: True`

Enables conditioning on a CATH label at the level defined by `cath_code_level: "T"` (Topology). Without this, sampling is unconditional.

#### `guidance_weight`

Controls CFG strength. The value in the config (`1.015415`) was found by Bayesian HPO — see section 7.

| Weight | Effect |
|---|---|
| < 1.0 | High diversity, weak fold control |
| ~1.0 (Bayesian optimum) | Fold correctness maximized for 2.60.40 at length 95 |
| > 3.0 | Strict fold adherence, reduced diversity |

#### `sampling_mode: sc` / `sc_scale_noise` (= `caflow_noise_scale`)

Uses SDE sampling with controlled noise injection. SDE (`sc`) produces more diverse outputs than ODE (`vf`). The noise scale (`0.262678`, Bayesian-optimized) avoids both mode collapse and structural instability.

---

## 3. ProteinMPNN — Sequence Design

Solves inverse folding: given a fixed backbone, design amino acid sequences predicted to fold into it.

### Invocation

```bash
python protein_mpnn_run.py \
    --ca_only \
    --pdb_path "<pdb>" \
    --out_folder ./ \
    --num_seq_per_target 200 \
    --sampling_temp "0.925228" \
    --seed 37
```

### Key Parameters

#### `--ca_only`

Uses only Cα coordinates instead of full-atom structure.

Proteína generates Cα-only backbones (no sidechains). Running ProteinMPNN in `--ca_only` mode makes it consistent with this input — both node and edge features are derived purely from Cα positions.

#### `--num_seq_per_target 200`

Generates 200 candidate sequences per backbone.

The sequence→structure mapping is many-to-one: many sequences can fold into the same backbone. 200 sequences per backbone increases the probability of recovering at least one that is thermodynamically stable and CATHe-consistent.

#### `--sampling_temp 0.925228`

Controls sequence diversity during autoregressive decoding.

| Temperature | Effect |
|---|---|
| 0.1–0.3 | Conservative, high-confidence sequences; low diversity |
| 0.5–0.9 | Balanced diversity and stability |
| **0.925228 (Bayesian optimum)** | High diversity; maximizes immunoglobulin hit rate at length 95 |
| > 1.0 | Very diverse; increased risk of unfolded outputs |

The high temperature (relative to ProteinMPNN's typical 0.1–0.3 range) reflects the HPO finding that diversity matters more than per-sequence confidence for hitting the target fold at scale.

### Role in the Pipeline

```
Backbone (Proteína)    ← Cα-only PDB
       ↓
  ProteinMPNN          ← inverse folding (200 sequences, T=0.925228, Cα-only)
       ↓
     CATHe2            ← fold classification & filtering
```

---

## 4. CATHe2 — Fold Classification

Classifies designed sequences into CATH superfamilies. Serves as the primary filter — only sequences the model predicts to be 2.60.40.x pass to the output.

### Invocation (as run in the pipeline)

The pipeline merges all FASTA outputs from ProteinMPNN, copies them to CATHe2's fixed input path, and runs classification from inside the CATHe2 root directory:

```bash
cat *.fa > merged.fasta
cp merged.fasta external/CATHe2/src/cathe-predict/sequences.fasta
cd external/CATHe2
python src/cathe-predict/cathe_predictions.py --model ProstT5 --input_type AA
```

CATHe2 writes its output to a `Results.csv` inside its own directory tree; the pipeline locates it with `find` and copies it to the Nextflow working directory as `classifications.csv`.

CATHe2 runs in a Python venv (`external/CATHe2/venv_2`) rather than a conda env because it needs to be invoked from within its own directory structure.

### Output columns

| Column | Description |
|---|---|
| `Sequence` | Amino acid sequence |
| `CATHe_Predicted_SFAM` | Predicted CATH superfamily (e.g. `2.60.40.10`) |
| `CATHe_Prediction_Probability` | Confidence score (0–1) |
| `Record` | ProteinMPNN FASTA header (`T=`, `global_score=`, `seq_recovery=`) |

### Why `--input_type AA` (AA-only, no 3Di)

CATHe2 can accept both amino acid sequences (`AA`) and 3Di structural alphabet sequences (`AA+3Di`). The pipeline uses AA-only because:
- No PDB structures are available at this stage — only sequences output by ProteinMPNN.
- AA-only still achieves strong classification performance; the heavy lifting is done by the ProstT5 language model embeddings.

### Role in the Pipeline

| Use | Description |
|---|---|
| Primary filter | Keeps sequences predicted as 2.60.40.x |
| Confidence threshold | `top_designs.csv` contains all 2.60.40 hits; `best_designs.csv` applies ≥ 98% cutoff |
| HPO objective | `pct_target_fold_high_conf` drives Bayesian optimization |

---

## 5. Nextflow Pipeline (main.nf)

Orchestrates the full design-validate-filter loop as a directed acyclic graph (DAG) of processes. Each process runs in an isolated working directory under `.nextflow/work/`.

### Process: GENERATE_BACKBONES

**Env:** `proteina_env` (conda)

Calls `inference_cond_sampling.py` with Hydra overrides sourced from `nextflow.config`. After generation, all `.pdb` files are moved to a `backbones/` subdirectory.

**Output channel:** `backbones/*.pdb`

---

### Process: RUN_MPNN

**Env:** `proteina_env` (conda)

Runs ProteinMPNN on a **single PDB file**. Nextflow's `.flatten()` splits the backbone channel so this process runs in parallel across all backbones — each backbone is processed independently.

**Input:** one `.pdb` file  
**Output channel:** `seqs/*.fa`

---

### Process: RUN_CATHE

**Env:** `external/CATHe2/venv_2` (Python venv, activated via `beforeScript`)

Receives all FASTA files at once (gathered with `.collect()`), merges them into a single batch, and runs CATHe2 classification on the full set.

**Input:** all `.fa` files from RUN_MPNN  
**Output:** `classifications.csv`

---

### Process: GENERATE_REPORT

**Env:** `protein_design_env` (conda)

Runs `src/generate_report.py`. Filters `classifications.csv` to sequences where `CATHe_Predicted_SFAM` contains `"2.60.40"`, computes per-length statistics, and generates a sequence diversity heatmap (normalized Levenshtein distance on up to 50 sequences).

**Input:** `classifications.csv`  
**Output:** `report.html`, `top_designs.csv`

`top_designs.csv` columns: `Sequence`, `CATHe_Prediction_Probability`, `CATHe_Predicted_SFAM`, `seq_len`, `temperature`, `global_score`, `seq_recovery` — sorted by probability descending.

---

### Process: LOG_RUN

**Env:** `protein_design_env` (conda)

Generates a unique `run_id` (`YYYYMMDD_HHMMSS_<6 hex chars>`), runs `src/log_run.py` to append metrics to `results/experiments.csv`, and copies all artifacts to a per-run subdirectory.

**Inputs:** `classifications.csv`, `report.html`, `top_designs.csv`  
**Side effects:** writes to `results/experiments.csv` and `results/artifacts/<run_id>/`

---

### Workflow Orchestration

```nextflow
workflow {
    backbones_ch = GENERATE_BACKBONES()
    pdb_ch       = backbones_ch.pdbs.flatten()          // one pdb per channel item
    fastas_ch    = RUN_MPNN(pdb_ch)                     // parallel over all pdbs
    cathe_ch     = RUN_CATHE(fastas_ch.fastas.collect()) // all fastas in one batch
    report_ch    = GENERATE_REPORT(cathe_ch)
    LOG_RUN(cathe_ch, report_ch.html, report_ch.csv)
}
```

- `.flatten()` splits the PDB list into individual items → RUN_MPNN runs once per PDB file in parallel.
- `.collect()` waits for all RUN_MPNN processes to finish before starting RUN_CATHE → classification runs on the full batch.

---

## 6. Pipeline Configuration (nextflow.config)

All parameters live in `pipeline/nextflow.config` and can be overridden on the command line.

### Environment and Script Paths

| Parameter | Value |
|---|---|
| `params.protein_design_env` | `/opt/miniconda3/envs/protein_design_env` |
| `params.proteina_env` | `/opt/miniconda3/envs/proteina_env` |
| `params.cathe_venv` | `external/CATHe2/venv_2` |
| `params.proteina_script` | `external/proteina/script_utils/inference_cond_sampling.py` |
| `params.mpnn_script` | `external/proteina/ProteinMPNN/protein_mpnn_run.py` |

### Tunable Parameters

The current defaults are the Bayesian-optimized values for length 95. See section 7 for how these were found.

| Parameter | Default | What it controls |
|---|---|---|
| `proteina.nsamples` | `10` | Number of backbones to generate |
| `proteina.nres_lens` | `[95]` | Protein length(s) to generate |
| `proteina.seed` | `5` | Proteína random seed |
| `proteina.dt` | `0.0025` | SDE integration step size |
| `proteina.guidance_weight` | `1.015415` | CFG strength |
| `proteina.autoguidance_ratio` | `0.792596` | Autoguidance correction weight |
| `proteina.sampling_mode` | `"sc"` | `"sc"` = SDE, `"vf"` = ODE |
| `proteina.caflow_noise_scale` | `0.262678` | SDE noise injection amplitude |
| `mpnn.num_seq_per_target` | `200` | Sequences designed per backbone |
| `mpnn.sampling_temp` | `0.925228` | ProteinMPNN sampling temperature |
| `mpnn.seed` | `37` | ProteinMPNN random seed |

### Overriding Parameters on the Command Line

```bash
# Run with multiple lengths
nextflow run main.nf -with-conda --proteina.nres_lens "95,100,105,110,115"

# Override individual generative parameters
nextflow run main.nf -with-conda \
    --proteina.guidance_weight 2.0 \
    --proteina.caflow_noise_scale 0.3

# Resume after a partial failure
nextflow run main.nf -with-conda -resume
```

---

## 7. Bayesian HPO (bayes_opt.py)

`src/bayes_opt.py` wraps the Nextflow pipeline in an Optuna optimization loop. Each trial is one full pipeline run; the objective is to maximize `pct_target_fold_high_conf` for a single target length.

### Search Space

| Parameter | Range |
|---|---|
| `guidance_weight` | 0.5 – 4.0 |
| `autoguidance_ratio` | 0.0 – 1.0 |
| `caflow_noise_scale` | 0.2 – 0.6 |
| `sampling_temp` | 0.1 – 1.0 |

(`sampling_temp` here is ProteinMPNN's temperature, passed as `--mpnn.sampling_temp`.)

### How a Trial Works

1. Optuna's TPE sampler proposes a parameter set.
2. `bayes_opt.py` invokes the pipeline as a subprocess:
   ```bash
   nextflow run main.nf -with-conda \
       --proteina.guidance_weight <v> \
       --proteina.autoguidance_ratio <v> \
       --proteina.caflow_noise_scale <v> \
       --mpnn.sampling_temp <v> \
       --proteina.nres_lens <N>
   ```
3. After the pipeline completes, `experiments.csv` is read to find the new `run_id` and retrieve `pct_target_fold_high_conf` for the target length.
4. The metric is returned to Optuna, which updates its surrogate model.

Each study is length-specific and persisted as a SQLite database at `results/optuna_hpo_len<N>.db`.

### Warm-Start

On startup (unless `--no-warmup`), the script seeds the study with all prior rows for that length from `experiments.csv`. This means any pipeline runs performed before HPO are automatically incorporated — no wasted experiments.

### Output

```json
// results/best_params_per_length.json
{
  "95": {
    "study_name": "hpo_len95",
    "n_completed_trials": 40,
    "best_pct_target_fold_high_conf": 63.4,
    "best_params": {
      "guidance_weight": 1.015415,
      "autoguidance_ratio": 0.792596,
      "caflow_noise_scale": 0.262678,
      "sampling_temp": 0.925228
    }
  }
}
```

The values in `nextflow.config` were copied from this file after HPO completed.

---

## 8. Post-Pipeline Scripts

These scripts run after one or more pipeline runs are complete. They are not part of the Nextflow DAG.

---

### concat_designs.py

Reads all `top_designs.csv` files from `results/artifacts/*/`, deduplicates by sequence, applies a confidence filter, and writes consolidated outputs.

**Probability threshold:** `CATHe_Prediction_Probability > 0.98`

| Output file | Contents |
|---|---|
| `results/all_designs.csv` | All unique 2.60.40 sequences across all runs |
| `results/best_designs.csv` | Subset with CATHe probability > 98%, sorted descending |
| `results/best_designs.fasta` | Same sequences in FASTA format (`>seq_0`, `>seq_1`, …) |

`best_designs.fasta` is the input for ESMFold structure prediction.

---

### final_validation.py

Cross-references CATHe2 sequence classification with FoldSeek structural search results to produce the final validated candidate set.

**Inputs:**
- `results/best_designs.csv`
- `results/foldseek/foldseek_results.txt`

**Parsing:**
- `seq_id` is extracted from the FoldSeek query name using the regex `seq_\d+` (ProteinMPNN appends `_ptm` and other suffixes to sequence IDs in FASTA headers).
- `cath_hit` is extracted from the FoldSeek target name using the regex `\d+\.\d+\.\d+\.\d+$`.

**FoldSeek output columns:** `query`, `target`, `fident`, `alnlen`, `mismatch`, `gapopen`, `qstart`, `qend`, `tstart`, `tend`, `evalue`, `bits`

**Validation logic:**

| Check | Condition | Use |
|---|---|---|
| `exact_cath_match` | FoldSeek hit CATH == `CATHe_Predicted_SFAM` | Diagnostic only (printed to stdout) |
| `has_2_60_40_hit` | Any FoldSeek hit starts with `"2.60.40."` | Selection criterion for final output |

Sequences passing `has_2_60_40_hit`, up to 200, are written to the output files.

| Output file | Contents |
|---|---|
| `results/best_200_validated_sequences.txt` | Final sequences as plain text (one per line) |
| `results/best_200_validated_sequences.fasta` | Same in FASTA format (`>seq_0`, …) |

---

## 9. Artifact Layout

```
results/
├── experiments.csv                     # one row per (run, length); all params + metrics
├── best_params_per_length.json         # best HPO params per length (if HPO was run)
├── optuna_hpo_len<N>.db                # Optuna SQLite study DB per target length
│
├── all_designs.csv                     # all unique 2.60.40 sequences across all runs
├── best_designs.csv                    # CATHe prob > 98%
├── best_designs.fasta                  # same, FASTA (input for ESMFold)
│
├── best_200_validated_sequences.txt    # final output: confirmed by CATHe2 + FoldSeek
├── best_200_validated_sequences.fasta  # same, FASTA
│
├── artifacts/
│   └── <run_id>/                       # one directory per pipeline run
│       ├── classifications.csv         # full CATHe2 output for this run
│       ├── report.html                 # per-length stats + diversity heatmap
│       └── top_designs.csv             # all 2.60.40 hits from this run
│
└── foldseek/
    ├── esmfold_best_designs/           # ESMFold PDB files go here before FoldSeek
    └── foldseek_results.txt            # FoldSeek search output (tab-separated)
```

`run_id` format: `YYYYMMDD_HHMMSS_<6 hex chars>` — generated at the end of each Nextflow run by `log_run.py`.
