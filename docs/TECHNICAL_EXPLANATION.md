# Protein Design Pipeline: Technical Documentation

> End-to-end guide covering Proteína, ProteinMPNN, CATHe, and Nextflow orchestration
> for structure-conditioned protein sequence design.

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

Proteína is the core generative model in the pipeline. It is a **flow-matching-based protein backbone generator** that maps Gaussian noise → 3D protein structures conditioned on a target fold class.

### Invocation

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples 1
```

**What this does:**
- Samples protein backbones conditioned on a CATH fold class
- Uses flow-matching sampling (SDE-based) to generate Cα coordinates
- Applies autoguidance + classifier-free guidance for structural quality

### 1.1 Argument Explanation

#### `--cath_codes 2.60.40.x`

This is the most important conditioning signal. It restricts sampling to a narrow structural manifold by specifying the full CATH hierarchy:

| Level | Value | Meaning |
|---|---|---|
| Class | `2` | Mainly β-class proteins |
| Architecture | `60` | β-sandwich-like structures |
| Topology | `40` | Specific structural family |
| Homology | `x` | Wildcard (any superfamily) |

**Effect:**
- Reduces the generative search space to a specific fold family
- Improves fold consistency, designability, and downstream ProteinMPNN success rate

#### `--config_name inference_cond_autoguidance`

Selects the sampling strategy. This config enables:
- **Classifier-free guidance (CFG)** — aligns outputs with the target CATH label
- **Autoguidance (AG)** — uses a checkpoint difference to correct the vector field

**Effect:**
- Removes "collapsed" or geometrically unrealistic backbones
- Improves structural sharpness and fold adherence

### 1.2 Configuration Explanation

```yaml
defaults:
  - inference_base
  - _self_

run_name_: cond_autoguidance
ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt
autoguidance_ckpt_path: "/path/to/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"
self_cond: True
fold_cond: True
cath_code_level: "T"   # Guidance level
guidance_weight: 2.0
sampling_caflow:
  sampling_mode: sc    # "vf" for ODE, "sc" for SDE
  sc_scale_noise: 0.3  # noise scale, used if sampling_mode == "sc"
```

#### `ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt`

The largest and best-performing model checkpoint:
- Trained on 21M AFDB-filtered structures
- ~400M parameters with triangle multiplicative updates

**Why this checkpoint:**
- Best long-chain performance (300–800 residues)
- Best fold diversity across CATH space
- Best designability scores in benchmarks

#### `autoguidance_ckpt_path`

A weaker, early-training checkpoint (~10k steps). It acts as a learned correction term: the difference between the strong and weak model's vector fields is used to sharpen outputs, improving geometric precision and designability without retraining.

#### `self_cond: True`

Self-conditioning feeds the previous timestep's prediction back into the model as an additional input.

**Effect:**
- Reduces sampling noise across timesteps
- Improves structural coherence
- Stabilizes generation for longer chains

#### `fold_cond: True`

Enables conditioning on the CATH class at the C/A/T hierarchy level. This is the primary **controllability mechanism** of Proteína — without it, sampling is unconditional.

#### `guidance_weight: 2.0`

Controls classifier-free guidance (CFG) strength:

| Weight | Effect |
|---|---|
| < 1.0 | High diversity, weak fold control |
| **2.0 (chosen)** | Balanced: fold correctness without mode collapse |
| > 3.0 | Strict fold adherence, reduced diversity |

#### `sampling_mode: sc` and `sc_scale_noise: 0.3`

```yaml
sampling_caflow:
  sampling_mode: sc    # stochastic differential equation sampling
  sc_scale_noise: 0.3  # noise injection scale
```

- `sc` (SDE) produces more diverse outputs than `vf` (ODE)
- Required for realistic protein variability; ODE sampling collapses to lower-entropy outputs
- `sc_scale_noise: 0.3` maintains stable noise injection; avoids both mode collapse and structural noise

### 1.3 Why This Setup Works

This configuration implements **hierarchical conditional flow matching with dual guidance**. The model is steered by four complementary signals simultaneously:

| Signal | Controls |
|---|---|
| CATH label | Macro-level fold class |
| CFG | Semantic alignment to target fold |
| Autoguidance | Physical realism correction |
| Self-conditioning | Temporal consistency across timesteps |

Together, these ensure that generated backbones are both fold-consistent and geometrically realistic before any sequence design occurs.

---

## 2. ProteinMPNN — Sequence Design

ProteinMPNN designs amino acid sequences given a **fixed backbone structure**.
It solves the inverse folding problem: given a 3D shape, find sequences that fold into it.

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

Use only Cα coordinates instead of full-atom structure.

**Why:**
- Proteína generates backbone-only structures (no sidechains)
- Simplifies downstream conditioning
- Improves robustness for noisy or flow-generated backbones

#### `--num_seq_per_target 50`

Generate 50 candidate sequences per backbone.

**Why:**
- Sequence→structure mapping is many-to-one; multiple valid sequences can fold into the same shape
- Increases probability of recovering at least one sequence that is thermodynamically stable, foldable, and CATHe-consistent

#### `--sampling_temp 0.3`

Controls sequence diversity during sampling.

| Temperature | Effect |
|---|---|
| Low (0.1–0.3) | Conservative, high-confidence sequences |
| High (0.5–1.0) | Diverse but less reliable |
| **0.3 (chosen)** | Prioritizes fold stability; reduces unfolded outputs |

### Role in the Pipeline

ProteinMPNN sits at the center of the **backbone → sequence → fold validation** loop:

```
Backbone (Proteína)
       ↓
  ProteinMPNN          ← inverse folding
       ↓
  ESMFold              ← structure prediction
       ↓
  CATHe                ← fold classification & filtering
```

---

## 3. CATHe — Fold Validation

CATHe classifies designed sequences into the CATH structural hierarchy,
providing fold-level validation independent of ESMFold.

### Invocation

```bash
python src/cathe-predict/cathe_predictions.py \
    --model ProstT5 \
    --input_type AA \
    --fasta outputs/sequences/seqs.fa \
    --out_csv outputs/metrics/cathe_labels.csv
```

### Purpose

CATHe assigns each sequence a **CATH structural classification**:

```
C → Class       (alpha, beta, alpha/beta, ...)
A → Architecture
T → Topology    (fold family)
H → Homologous superfamily
```

### Why ProstT5?

- Strong protein language model trained on evolutionary sequence data
- Captures both evolutionary signal and structural context
- Outperforms ESM-based classifiers on fold classification benchmarks

### Role in the Pipeline

| Use | Description |
|---|---|
| Fold consistency check | Verify predicted fold matches the intended CATH class |
| Sequence filtering | Discard sequences assigned to the wrong fold family |
| Comparative analysis | Compare predicted vs. target CATH label across all outputs |

---

## 4. Nextflow Pipeline

Nextflow orchestrates the full design-validate-filter loop as a
**directed acyclic graph (DAG)** of processes.

### Pipeline Structure

```
┌─────────────────────────────────────────────────────────┐
│                   PIPELINE OVERVIEW                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Proteína (backbone generation, CATH-conditioned)       │
│          │                                               │
│          ▼                                               │
│   ProteinMPNN (inverse folding, N=50 sequences)          │
│          │                                               │
│          ▼                                               │
│   ESMFold (structure prediction)                         │
│          │                                               │
│          ▼                                               │
│   CATHe (fold classification & filtering)                │
│          │                                               │
│          ▼                                               │
│   Filter & export designable sequences                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Why Nextflow?

#### 1. Reproducibility

Every run executes the **same DAG** with the same process graph.
No manual step ordering. No missed intermediate files.

#### 2. Parallelization

Multiple backbones are processed simultaneously across:
- Backbone sampling
- MPNN sequence design
- Structure prediction (ESMFold)
- Fold classification (CATHe)

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

#### 3. Fault Tolerance

If one sample fails (e.g., ESMFold OOM on a long sequence), the pipeline:
- Logs the failure
- Continues processing all remaining samples
- Reports failed samples in the final run summary

### `nextflow.config` — Key Parameters

```groovy
params {
    // Backbone generation
    num_backbones     = 100
    length_min        = 95
    length_max        = 115

    // ProteinMPNN
    num_seqs          = 50
    sampling_temp     = "0.3"
    ca_only           = true

    // Guidance weights
    cfg_weight        = 2.0
    ag_weight         = 1.5
    noise_scale       = 0.3

    // Filtering
    cathe_match       = true
}
```

### Design Philosophy

> **"Generate many → filter aggressively → keep only designable proteins"**

This is necessary because:
- Flow matching models produce many geometrically marginal samples
- Biological validity is sparse in the raw output distribution
- CATHe filtering removes fold-inconsistent sequences before downstream use

---

## 5. Core Design Tactics

### 5.1 Hierarchical CATH Conditioning

Generation is **not blind**. Each backbone is conditioned on a target CATH label at the Topology (T) level:

```
Class (C) → Architecture (A) → Topology (T)
```

**Effect:**
- Reduces the generative search space to a single fold family
- Improves structural coherence of generated backbones
- Enables targeted fold design (e.g., "generate a β-sandwich")

### 5.2 Dual Guidance System

Two complementary forces guide backbone generation:

| Guidance | Mechanism | Effect |
|---|---|---|
| **CFG** (Classifier-Free Guidance) | Amplifies CATH-conditioned signal | Enforces fold adherence |
| **Autoguidance (AG)** | Vector field correction via strong–weak checkpoint contrast | Enforces physical geometry |

**Combined effect:** outputs are both structurally coherent *and* physically plausible — the two failure modes (wrong fold, bad geometry) are addressed independently.

### 5.3 Model Hierarchy for Autoguidance

| Model | Checkpoint | Role |
|---|---|---|
| **Strong** | `proteina_v1.4_D21M_400M_tri.ckpt` (21M dataset) | Primary generation |
| **Weak** | Early checkpoint (~10k steps) | Autoguidance reference |

The strong–weak vector field difference acts as a correction term during sampling, improving geometry quality without requiring additional training data or fine-tuning.

### 5.4 Parameter Reference Table

| Parameter | Value | Rationale |
|---|---|---|
| CFG weight | `2.0` | Balances fold control vs. diversity |
| AG weight | `~1.5` | Improves backbone geometry |
| Noise scale | `0.3` | Stable SDE sampling; avoids mode collapse |
| Length range | `95–115 aa` | Optimal designability window |
| Sampling mode | `sc` (SDE) | Better diversity than ODE (`vf`) |
| MPNN temp | `0.3` | Prioritizes sequence stability |
| Sequences/backbone | `50` | Sufficient coverage of sequence space |
| CATH guidance level | `T` (Topology) | Specific enough for fold control; general enough for diversity |

---

## 6. Reproducible Commands

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

> `-resume` restores cached process outputs — use it to avoid re-running completed steps after a partial failure.

---

### Step 1 — Backbone Generation (Proteína)

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples 100
```

For a different fold class (e.g., TIM barrel `3.20.20`):

```bash
python inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 3.20.20.x \
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

### Step 3 — Structure Prediction (ESMFold)

```bash
python src/esmfold_predict.py \
    --fasta outputs/sequences/seqs.fa \
    --out_dir outputs/esmfold/ \
    --chunk_size 128
```

---

### Step 4 — Fold Classification (CATHe)

```bash
python src/cathe-predict/cathe_predictions.py \
    --model ProstT5 \
    --input_type AA \
    --fasta outputs/sequences/seqs.fa \
    --out_csv outputs/metrics/cathe_labels.csv
```

---

### Step 5 — Filter by Fold Match

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
ProteinMPNN  →  50 candidate sequences per backbone (T=0.3, Cα-only)
    ↓
ESMFold      →  Structure prediction for each sequence
    ↓
CATHe        →  Fold classification; keep sequences matching target CATH class
    ↓
             Designable proteins ✓
```

The pipeline is conservative by design: high throughput at generation,
aggressive fold-based filtering at validation, small but reliable final output.