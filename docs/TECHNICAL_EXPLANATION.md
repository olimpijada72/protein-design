# Protein Design Pipeline: Technical Documentation
TO-DO list:
- TO-DO: make Filter & export designable sequences
- TO-DO: actually make a nextflow config that does this
- TO-DO make this pipeline run like this
- TO-DO add filtering step

> End-to-end technical guide for backbone generation, sequence design,
> fold validation, and Nextflow orchestration.

---

## Table of Contents

1. [Proteína — Backbone Generation](#1-proteína--backbone-generation)
2. [ProteinMPNN — Sequence Design](#2-proteinmpnn--sequence-design)
3. [CATHe — Fold Validation](#3-cathe--fold-validation)
4. [Nextflow Pipeline](#4-nextflow-pipeline)
5. [Core Design Tactics](#5-core-design-tactics)
6. [Reproducible Commands](#6-reproducible-commands)

---

## 1. Proteína — Backbone Generation

Flow-matching backbone generator: maps Gaussian noise → CATH-conditioned 3D protein structures.

### Invocation

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples 1
```

Samples CATH-conditioned backbones via SDE-based flow matching with CFG + autoguidance.

### Why This Works

Four complementary signals steer the model simultaneously:

| Signal | Controls |
|---|---|
| CATH label | Macro-level fold class |
| CFG | Semantic alignment to target fold |
| Autoguidance | Physical realism correction |
| Self-conditioning | Temporal consistency across timesteps |

Outputs are fold-consistent **and** geometrically realistic before any sequence design occurs.

---

### Key Arguments

#### `--cath_codes 2.60.40.x`

**What it does:** restricts sampling to a narrow structural manifold via the CATH hierarchy.

| Level | Value | Meaning |
|---|---|---|
| Class | `2` | Mainly β-class proteins |
| Architecture | `60` | β-sandwich-like structures |
| Topology | `40` | Specific structural family |
| Homology | `x` | Wildcard (any superfamily) |

**Why it matters:** reduces the generative search space to a single fold family; improves fold consistency and downstream MPNN success.

#### `--config_name inference_cond_autoguidance`

**What it does:** selects the sampling strategy; enables CFG + autoguidance correction.

**Why it matters:** removes geometrically collapsed backbones and improves fold adherence.

---

### Key Config Parameters

Two configs drive Proteína: `inference_base.yaml` (defaults) and `inference_cond_autoguidance.yaml` (overrides).

`inference_cond_autoguidance.yaml`
```yaml
defaults:
  - inference_base
  - _self_

run_name_: cond_autoguidance
ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt
autoguidance_ckpt_path: "/path/to/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"
self_cond: True
fold_cond: True
cath_code_level: "T"
guidance_weight: 2.0
sampling_caflow:
  sampling_mode: sc    # "vf" for ODE, "sc" for SDE
```

One important thing for `inference_base.yaml`: here we define  `nres_lens : [95, 100, 105, 110, 115]`. That means that proteina willg generate backbones of those lengths.


<details>
<summary>Full base config — inference_base.yaml</summary>

```yaml
run_name_: "testing_IgFold_2.60.40_Sweep"
ckpt_path: "/Users/mipopovic/Desktop/proteina/data/checkpoints"
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
autoguidance_ckpt_path: "/Users/mipopovic/Desktop/proteina/data/checkpoints/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"

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

#### `ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt`

**What it does:** loads the primary generation model (21M AFDB structures, ~400M parameters).

**Why it matters:** best long-chain performance (300–800 residues), fold diversity, and designability scores across benchmarks.

#### `autoguidance_ckpt_path`

**What it does:** loads a weaker early-training checkpoint (~10k steps) used as a geometry reference.

**Why it matters:** the strong–weak vector field difference acts as a correction term during sampling — improves physical realism without retraining.

| Component | Role |
|---|---|
| Strong checkpoint | Primary generation |
| Weak checkpoint | Geometry correction reference |
| Field difference | Autoguidance signal |

#### `self_cond: True`

**What it does:** feeds the previous timestep's prediction back into the model as an additional input.

**Why it matters:** reduces timestep noise and improves sampling stability for longer chains.

#### `fold_cond: True`

**What it does:** enables conditioning on the CATH class at the C/A/T hierarchy level.

**Why it matters:** the primary controllability mechanism — without it, sampling is unconditional.

#### `guidance_weight: 2.0`

**What it does:** controls CFG strength.

| Weight | Effect |
|---|---|
| < 1.0 | High diversity, weak fold control |
| **2.0 (chosen)** | Balanced: fold correctness without mode collapse |
| > 3.0 | Strict fold adherence, reduced diversity |

#### `sampling_mode: sc` / `sc_scale_noise: 0.3`

**What it does:** uses SDE sampling with controlled noise injection.

**Why it matters:** SDE (`sc`) produces more diverse outputs than ODE (`vf`); noise scale 0.3 avoids both mode collapse and structural instability.

---

## 2. ProteinMPNN — Sequence Design

Solves inverse folding: given a fixed backbone, design amino acid sequences that fold into it.

### Invocation

```bash
python ${params.mpnn_script} \
    --ca_only \
    --pdb_path "${pdb}" \
    --out_folder ./ \
    --num_seq_per_target 50 \
    --sampling_temp "0.3"
```

### Key Parameters

#### `--ca_only`

**What it does:** uses only Cα coordinates instead of full-atom structure.

**Why it matters:** Proteína generates backbone-only outputs (no sidechains); Cα-only improves robustness for flow-generated backbones.

#### `--num_seq_per_target 50`

**What it does:** generates 50 candidate sequences per backbone.

**Why it matters:** sequence→structure mapping is many-to-one; 50 sequences increases the probability of recovering at least one that is thermodynamically stable and CATHe-consistent.

#### `--sampling_temp 0.3`

**What it does:** controls sequence diversity during sampling.

| Temperature | Effect |
|---|---|
| 0.1–0.3 | Conservative, high-confidence sequences |
| **0.3 (chosen)** | Prioritizes fold stability; reduces unfolded outputs |
| 0.5–1.0 | Diverse but less reliable |

### Role in the Pipeline

```
Backbone (Proteína)
       ↓
  ProteinMPNN          ← inverse folding
       ↓
     CATHe             ← fold classification & filtering
```

---

## 3. CATHe — Fold Validation

Classifies designed sequences into the CATH structural hierarchy — fold-level validation independent of ESMFold.

### Invocation

```bash
python src/cathe-predict/cathe_predictions.py \
    --model ProstT5 \
    --input_type AA \
    --fasta outputs/sequences/seqs.fa \
    --out_csv outputs/metrics/cathe_labels.csv
```

### CATH Hierarchy

```
C → Class       (alpha, beta, alpha/beta, ...)
A → Architecture
T → Topology    (fold family)
H → Homologous superfamily
```

### Why ProstT5?

Protein language model trained on evolutionary sequence data; captures both evolutionary signal and structural context. Outperforms ESM-based classifiers on fold classification benchmarks.

### Role in the Pipeline

| Use | Description |
|---|---|
| Fold consistency | Verify predicted fold matches intended CATH class |
| Sequence filtering | Discard sequences assigned to the wrong fold family |
| Comparative analysis | Compare predicted vs. target CATH label across all outputs |

---

## 4. Nextflow Pipeline

Orchestrates the full design-validate-filter loop as a **directed acyclic graph (DAG)** of processes.

### Pipeline Structure
TO-DO: make Filter & export designable sequences

```
Proteína     →  CATH-conditioned backbone generation (for lengths defined in nres_lens)
     ↓
ProteinMPNN  →  inverse folding (50 sequences/backbone)
     ↓
CATHe        →  fold classification & filtering
     ↓
Filter & export designable sequences
```

### Why Nextflow?

| Property | What it provides |
|---|---|
| **Reproducibility** | Same DAG every run; no manual step ordering; no missed intermediates |
| **Parallelization** | Backbone sampling, MPNN design, ESMFold, and CATHe run concurrently |
| **Fault tolerance** | Per-sample failures are logged; remaining samples continue unaffected |

Example process definition:

```nextflow
process MPNN_DESIGN {
    input:
        path pdb
    output:
        path "seqs/*.fa"

    script:
    """
    python ${params.mpnn_script} \
        --ca_only \
        --pdb_path ${pdb} \
        --out_folder ./ \
        --num_seq_per_target ${params.num_seqs} \
        --sampling_temp ${params.temp}
    """
}
```
TO-DO: actually make a nextflow config that does this
### `nextflow.config` — Key Parameters

```groovy
params {
    num_backbones     = 100
    length_min        = 95
    length_max        = 115

    num_seqs          = 50
    sampling_temp     = "0.3"
    ca_only           = true

    cfg_weight        = 2.0
    ag_weight         = 1.5
    noise_scale       = 0.3

    cathe_match       = true
}
```

### Design Philosophy

> **"Generate many → filter aggressively → keep only designable proteins"**

Flow matching produces many geometrically marginal samples. Biological validity is sparse in the raw output distribution. CATHe filtering removes fold-inconsistent sequences before downstream use.

---

## 5. Core Design Tactics

### Hierarchical CATH Conditioning

Each backbone is conditioned on a target CATH label at the Topology (T) level:

```
Class (C) → Architecture (A) → Topology (T)
```

Reduces the generative search space to a single fold family; enables targeted fold design (e.g., "generate a β-sandwich").

### Dual Guidance System

| Guidance | Mechanism | Effect |
|---|---|---|
| **CFG** | Amplifies CATH-conditioned signal | Enforces fold adherence |
| **Autoguidance** | Vector field correction via strong–weak checkpoint contrast | Enforces physical geometry |

The two failure modes — wrong fold and bad geometry — are addressed independently.

### Model Hierarchy for Autoguidance

| Model | Checkpoint | Role |
|---|---|---|
| **Strong** | `proteina_v1.4_D21M_400M_tri.ckpt` | Primary generation |
| **Weak** | Early checkpoint (~10k steps) | Geometry correction reference |

### Parameter Reference

| Parameter | Value | Rationale |
|---|---|---|
| CFG weight | `2.0` | Balances fold control vs. diversity |
| AG weight | `~1.5` | Improves backbone geometry |
| Noise scale | `0.3` | Stable SDE sampling; avoids mode collapse |
| Length range | `95–115 aa` | Optimal designability window |
| Sampling mode | `sc` (SDE) | Better diversity than ODE (`vf`) |
| MPNN temp | `0.3` | Prioritizes sequence stability |
| Sequences/backbone | `50` | Sufficient coverage of sequence space |
| CATH guidance level | `T` | Specific enough for fold control; general enough for diversity |

---

## 6. Reproducible Commands

TO-DO make this pipeline run like this
### Full Pipeline Run

```bash
nextflow run main.nf \
    --cath_class "2.60.40" \
    --num_backbones 100 \
    --num_seqs 50 \
    --cfg_weight 2.0 \
    --ag_weight 1.5 \
    --sampling_temp 0.3 \
    -profile gpu \
    -resume
```

> `-resume` restores cached process outputs — skips completed steps after a partial failure.

---

### Step 1 — Backbone Generation (Proteína)

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples 100
```

---

### Step 2 — Sequence Design (ProteinMPNN)

```bash
# Single PDB
python /path/to/protein_mpnn_run.py \
    --ca_only \
    --pdb_path outputs/backbones/sample_001.pdb \
    --out_folder outputs/sequences/ \
    --num_seq_per_target 50 \
    --sampling_temp 0.3

# Batch — all PDBs in a folder
for pdb in outputs/backbones/*.pdb; do
    python /path/to/protein_mpnn_run.py \
        --ca_only \
        --pdb_path "${pdb}" \
        --out_folder outputs/sequences/ \
        --num_seq_per_target 50 \
        --sampling_temp 0.3
done
```

---

### Step 3 — Fold Classification (CATHe)

```bash
python src/cathe-predict/cathe_predictions.py \
    --model ProstT5 \
    --input_type AA \
    --fasta outputs/sequences/seqs.fa \
    --out_csv outputs/metrics/cathe_labels.csv
```

---


TO-DO add filtering step
### Step 4 — Filter by Fold Match

```bash
python src/filter_designable.py \
    --cathe_csv outputs/metrics/cathe_labels.csv \
    --target_cath 2.60.40 \
    --out_fasta outputs/final/designable_sequences.fa
```

---

## Summary

```
Proteína     →  CATH-conditioned backbone generation (CFG + AG + self-cond)
     ↓
ProteinMPNN  →  50 sequences per backbone (T=0.3, Cα-only)
     ↓
ESMFold      →  structure prediction
     ↓
CATHe        →  fold classification; keep sequences matching target CATH
     ↓
             Designable proteins ✓
```

High throughput at generation, aggressive fold-based filtering at validation, small but reliable final output.
