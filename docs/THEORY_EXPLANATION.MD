# Explanation of Theoretical Aspects 

## Table of Contents

1. [Protein Biology Fundamentals](#1-protein-biology-fundamentals)
2. [Protein Representation in Machine Learning](#2-protein-representation-in-machine-learning)
3. [How Proteina Works?](#3-how-proteina-works)
4. [How ProteinMPNN Works?](#4-how-proteinmpnn-works)
5. [How CATHe2 Works?](#5-how-cathe2-works)
6. [How ESMFold Works?](#6-how-esmfold-works)
7. [How FoldSeek Works?](#7-how-foldseek-works)
8. [Bayesian Hyperparameter Optimization](#8-bayesian-hyperparameter-optimization)
9. [Pipeline Integration](#9-pipeline-integration)


---

## 1. Protein Biology Fundamentals

### 1.1. What is a Protein and What is it Made of?
Proteins are biological macromolecules composed of amino acid chains whose three-dimensional structure determines their function. In computational protein design, proteins are typically represented either as amino acid sequences or as 3D atomic coordinates, depending on the modeling task.

Each amino acid has:
- **Backbone**: Same structure in all amino acids (–NH₂, –COOH).
- **Side chain (R group)**: Gives each amino acid its chemical properties (hydrophobic, polar, charged).
The sequence of amino acids determines the protein’s shape and function.

![protein diagram](/figures/protein_diagram.png)


An **amino acid residue**ma is the portion of an amino acid that remains after it has formed a peptide bond with other amino acids in a protein or peptide chain, losing a molecule of water in the process; it's the fundamental building block of proteins.

The **alpha (α) carbon** is the central carbon atom of an amino acid. It is bonded to:
- the amino group (–NH₂)
- the carboxyl group (–COOH)
- a hydrogen atom
- the side chain (R-group)

In proteins, the Cα atoms form the backbone trace of the structure and are commonly used in computational protein modeling.

![peptide bond](/figures/peptide_bond_diagram.png)


### 1.2. Protein Structure
There are 4 different structural levels at which proteins are observed


1. Primary - The Sequence
    - Simply the **sequence of amino acids** written from the **N terminus** (amino end) to the **C terminus** (Carboxyl end)
    - Determines everything about the protein’s final shape and function. Even a single amino acid change can cause major effects (e.g., sickle cell anemia from a single substitution in hemoglobin).

2. Secondary Structure — Local Folding Patterns
    - Localized conformation of the chain, i.e. **the folding pattern over a few dozen amino acid residues**
    - Provides structural stability and scaffolding for the protein’s shape.
    - Main types:
        - **α-helix** - A right-handed coil stabilized by hydrogen bonds every 4 residues (keratin in hair).
        - **β-sheet** — Strands linked side-by-side; can be parallel or antiparallel (silk fibroin).

3. Tertiary Structure — Overall 3D Shape
    - The full 3D arrangement of the entire polypeptide chain, including how secondary structures pack together.
    - Defines the protein’s active sites and binding surfaces.

4. Quaternary Structure — Multiple Subunits
    - The arrangement of multiple polypeptide chains (subunits) into one functional protein complex.
    - Allows cooperative behavior, regulation, and complex functions.
    - Example: Hemoglobin — 4 subunits work together to transport oxygen.

![Protein structures](/figures/protein_structures.png)


### 1.3. Key Functional Categories
Different protein structures enable different biological functions. Major functional categories include:
- Enzymes — Catalyze biochemical reactions.
- Transport proteins — Hemoglobin, ion channels.
- Signaling proteins — Hormones, receptors.
- Structural proteins — Actin, collagen.
- Defense proteins — Antibodies.

### 1.4. CATH Classification System
CATH (Class – Architecture – Topology – Homologous superfamily) is a hierarchical classification system that organizes protein domains based on their **3D structural features** and **evolutionary relationships.** There are 4 levels:
1. **Class (C)**
    - Broadest category, based on **secondary structure composition.**
    - Example:
        - Mainly α (helices dominate)
        - Mainly β (sheets dominate) 
        - α–β mixed
2. **Architecture (A)**
    - **Arrangement of secondary structures in 3D space**, ignoring connectivity.
    - Example: β-barrel, α-sandwich, α–β horseshoe.
    - Captures the *overall shape of the domain.*
3. **Topology (T)**
    - Also called **fold.**
    - Includes **connectivity/order of secondary structures.**
    - Example: TIM barrel fold (α/β-barrel).
    - Domains with the same topology often evolved from a common ancestor.
4. **Homologous superfamily (H)**
    - Groups domains with **clear evidence of evolutionary relationship.**
    -  Members share similar structures and often related functions.

![CATH system](/figures/cath_system.png)


### 1.5. Immunoglobulin (Ig)
- Immunoglobulin is a protein family with the **immunoglobulin fold** (β-sandwich of antiparallel β-strands)
- **Antibodies are specialized immunoglobulins** produced by B cells that bind antigens
- All antibodies are immunoglobulins, but not all immunoglobulins act as antibodies. Think of immunoglobulin as the “category” (like *dog*), and antibody as a specific “job” some of those proteins have (like *guide dog*). All guide dogs are dogs, but not all dogs are guide dogs.

![immunoglobulin diagram.](/figures/immunoglobulin_diagram.png)

Immunoglobulin-like folds correspond to 2.60.40 in the CATH system:
- 2 → Class: Mainly β
- 60 → Architecture: β-barrel
- 40 → Topology (Fold family): Immunoglobulin-like β-sandwich
- So, 2.60.40 = the Ig-like β-sandwich fold.

## 2. Protein Representation in Machine Learning
### 2.1. File Formats
**FASTA** (`.fasta`, `.fa`)
 - Stores amino acid sequences as plain text. Each entry has a header line starting with > (protein ID / description) followed by the sequence string.
```
>protein_id description
ACDEFGHIKLMNPQRSTVWY...
```
**PDB** (`.pdb`)
- The Protein Data Bank format stores 3D atomic coordinates. Each ATOM record specifies the element, residue, chain, and (x, y, z) position in Ångströms.

```
ATOM      1  N   ALA A   1      11.751  12.123   8.901  1.00  0.00
```

### 2.2. Representations

**Sequences**
- A protein is first and foremost a string over a 20-letter alphabet (the standard amino acids). Sequences are the input and output of inverse folding — given a structure, recover a sequence that will fold into it.


**One-hot encoding**
- Each residue is encoded as a binary vector of length 20 with a single 1 at the position corresponding to its amino acid identity. Simple but loses any notion of similarity between amino acids.

**Embeddings**
- Dense, learned vector representations that capture biochemical and structural similarity. Protein language models (used in CATHe2) produce per-residue embeddings trained on millions of sequences; these compress evolutionary and structural information into fixed-size vectors.

**Structural graphs**
- A protein structure is represented as a graph where nodes are residues and edges connect spatially nearby residues (k-nearest neighbors in 3D space). ProteinMPNN operates on this representation, passing messages along edges to reason about local structural context.

**Coordinate systems**
- The 3D positions of backbone atoms (N, Cα, C, O) per residue, typically in Cartesian (x, y, z) space measured in Ångströms. Proteina works directly in this space during backbone generation and uses internal coordinates (bond lengths, angles, dihedrals) to parameterize conformational changes.

## 3. How Proteina Works?

Proteina (ICLR 2025) is a generative model for **de novo protein backbone design** — it creates protein 3D structures from scratch, without being given an input sequence or structure to build on.

### 3.1 What it generates

Proteina outputs **backbone coordinates** only: the (x, y, z) positions of the Cα atom for each residue in the chain. It does not design amino acid sequences (that is ProteinMPNN's job) and does not model side chains. A Cα-only backbone is enough to describe the protein's fold shape.

### 3.2 Diffusion vs Flow Matching

Both are generative frameworks that start from random noise and denoise toward real data.

**Diffusion** adds Gaussian noise to data through many small steps and trains the model to reverse each step. The forward and reverse processes are mathematically coupled, which makes training stable but sampling slow (many function evaluations needed).
![diffusion model](/figures/diffusion_model_diagram.png)

**Flow matching** is a simpler alternative. It directly learns a vector field — a function that, at any point in time, says *"move in this direction"* — that continuously transports samples from a noise distribution to the data distribution. Training is more straightforward and sampling can be done in fewer steps.

![flow_matching_diagran](/figures/flow_matching_diagram.png)
Proteina uses **flow matching** specifically: it learns a flow from random 3D Gaussian coordinates to physically plausible protein backbone shapes.

### 3.3 CATH Conditioning

Proteina is trained with **CATH fold class labels** as a conditioning signal. This allows the model to be told, at sampling time, what fold family to generate down to Class (C), Architecture (A), or Topology (T) level of the CATH hierarchy. In this pipeline, we condition on CATH code `2.60.40.x`, which corresponds to the **Ig-like β-sandwich fold** (see section 1.5).

To make conditioning stronger, Proteina supports:
- **Classifier-free guidance (CFG)**: the model is trained sometimes with and sometimes without the CATH label. At sampling time, predictions are shifted away from the unconditional direction, steering output toward the desired fold.
- **Autoguidance**: a weaker early checkpoint of the model replaces the unconditional signal, giving a softer guidance effect.

### 3.4 Architecture

Proteina uses a **transformer** (`ProteinTransformerAF3`) with up to 400M parameters. It optionally includes **triangular multiplicative update layers**, borrowed from AlphaFold 3, which model pairwise residue-residue relationships explicitly and improve geometric reasoning.

The model also uses **self-conditioning**: during generation, the model conditions on its own previous noisy prediction at each denoising step, which has been shown empirically to improve quality.

---

## 4. How ProteinMPNN Works?

ProteinMPNN solves **inverse folding**: given a protein backbone (the 3D structure), find amino acid sequences that are predicted to fold into it. This is the bridge between Proteina's backbone outputs and sequences that can be synthesized or evaluated.

![protein mpnn diagram](/figures/proteinmpnn_diagram.png)

### 4.1 Graph Representation

The backbone is converted into a **k-nearest-neighbor graph**:
- **Nodes**: residues. Node features encode local geometry (backbone dihedral angles, distances to neighbors).
- **Edges**: connect each residue to its ~48 spatially closest residues. Edge features encode relative orientations and distances between residue frames.

In the `--ca_only` mode used in this pipeline, only Cα positions are available, so both node and edge features are derived purely from those coordinates.

### 4.2 Message Passing

A stack of message-passing layers propagates information across the graph. At each layer, every node:
1. Collects messages from its neighbors (a weighted aggregation of neighbor representations).
2. Updates its own representation by combining the incoming messages with its current state.

After several rounds, each residue's representation encodes not just local geometry but also its broader structural context — which secondary structure it's part of, how it packs against other regions, etc.

### 4.3 Autoregressive Decoding

Sequences are decoded **one residue at a time**, but in a randomly shuffled order (not strictly N-to-C terminus). At each step, the model uses:
- The full structural graph.
- The identities of residues already decoded.

It outputs a probability distribution over the 20 amino acids for the current position and samples from it. The **temperature** parameter (0.3 in this pipeline) controls how peaked the distribution is: lower temperature → more conservative, higher-probability choices; higher temperature → more diverse, creative sequences.

Each backbone in this pipeline generates **50 candidate sequences**, trading off diversity against designability.

---

## 5. How CATHe2 Works?

CATHe2 classifies protein sequences (and optionally structures) into **CATH superfamilies**. In this pipeline it serves as a verification step — checking whether the sequences produced by ProteinMPNN are predicted to belong to the target Ig-like fold class.

### 5.1 Protein Language Models

A **protein language model (pLM)** is a large transformer model pretrained on millions of protein sequences (analogous to GPT for text). It learns statistical patterns of which amino acids co-occur, which are evolutionarily conserved, and which are structurally constrained — all without ever seeing 3D coordinates.

CATHe2 uses **ProstT5** (or alternatively Ankh), which can embed both:
- **AA sequences** — standard amino acid strings.
- **3Di sequences** — a structural alphabet (20 symbols) derived from the local 3D geometry of each residue, generated by Foldseek from PDB files.

The pLM produces a vector per residue. These are **mean-pooled** across the sequence to yield a single fixed-length vector representing the whole protein.

### 5.2 ANN Classifier

On top of the pLM embeddings, CATHe2 trains a shallow **artificial neural network (ANN)**, a feedforward network with a few dense layers, to classify the protein into a CATH superfamily. The ANN is fast and accurate because the pLM embedding has already done the heavy lifting of encoding relevant protein features.

Using `AA+3Di` input (both sequence and structural alphabet) yields ~92% accuracy; `AA` only still reaches strong performance, which is why this pipeline runs CATHe2 in AA-only mode — no structural input is needed at the classification stage.

---

## 6. How ESMFold Works?
![ESMFold architecture](/figures/esmfold_arch.jpg)
ESMFold (Meta AI Research, 2022) is a **sequence-to-structure predictor** — given an amino acid sequence, it predicts the full 3D atomic structure of the protein. In this pipeline it acts as a **post-pipeline structural validator**: after CATHe2 has classified sequences, the highest-confidence candidates (≥98% prediction probability) are folded into PDB structures so their geometry can be verified independently of sequence-based classification.

### 6.1 Protein Language Model Backbone

Unlike AlphaFold2, which requires a Multiple Sequence Alignment (MSA) of evolutionary relatives, ESMFold is **MSA-free**. It is built on top of **ESM-2**, a protein language model with 650M–15B parameters trained on ~250 million protein sequences. ESM-2 produces rich per-residue embeddings that encode evolutionary and structural information from a single input sequence alone.

This makes ESMFold:
- **Fast** — no MSA computation needed; structure prediction takes seconds per sequence.
- **Single-sequence** — ideal for *de novo* designed proteins that have no natural homologs to align against.

### 6.2 Structure Module

On top of the ESM-2 trunk, ESMFold adds a **folding trunk** and a **structure module** borrowed from AlphaFold2:
- The folding trunk processes pairwise residue-residue representations.
- The structure module uses **Invariant Point Attention (IPA)** to predict backbone rigid-body frames (rotation + translation) for each residue and iteratively refine them.
- Side chains are predicted via a torsion angle head applied to the refined backbone.

The output is a full-atom PDB file with per-residue **pLDDT** (predicted Local Distance Difference Test) confidence scores ranging from 0–100. High pLDDT (>70) indicates a confident, well-resolved prediction; low pLDDT indicates a disordered or uncertain region.


## 7. How FoldSeek Works?

FoldSeek (van Kempen et al., 2023) is a **structure-to-structure search tool** — it finds structurally similar proteins in large databases at speeds comparable to sequence search. In this pipeline it is used after ESMFold to verify that the predicted 3D structures of candidate sequences actually resemble known immunoglobulin proteins in the **CATH50 database**, providing a second, independent validation channel.

### 7.1 The 3Di Structural Alphabet

The key innovation in FoldSeek is the **3Di structural alphabet** — a 20-letter encoding of local 3D structural context. For each residue, FoldSeek:
1. Examines the spatial arrangement of the residue and its nearest 3D neighbors.
2. Assigns one of 20 discrete "structural letters" based on this local geometry.

This converts a 3D protein structure into a **1D string over a 20-symbol alphabet**, analogous to an amino acid sequence. CATHe2 uses 3Di sequences as one of its optional inputs (alongside amino acid sequences) for the same reason — local structural context compressed into a sequence-like representation.

### 7.2 Fast Structure Search

Once a structure is encoded as a 3Di string, structure-to-structure alignment reduces to **sequence alignment** — a much faster problem than full 3D superposition. FoldSeek applies the same dynamic programming algorithms used in MMseqs2 to align 3Di strings, achieving structural search **2–3 orders of magnitude faster** than tools like TM-align or DALI.

The search returns a tab-separated results file with: query name, target name, sequence identity (`fident`), alignment length, e-value, and bit score. The `final_validation.py` script reads this file to check whether each designed sequence has a structural hit classified as 2.60.40.x in CATH.

### 7.3 CATH50 Database

This pipeline searches against **CATH50**, a non-redundant database of CATH structural domains clustered at 50% sequence identity. Each entry carries its full CATH label (e.g., `2.60.40.10`), so FoldSeek hits can be directly cross-referenced against the target Ig-like fold family.


---

## 8. Bayesian Hyperparameter Optimization

The pipeline has four continuous parameters that strongly influence what fraction of generated sequences are correctly classified as immunoglobulin-like:

| Parameter | Controls |
|---|---|
| `guidance_weight` | Strength of CATH fold conditioning (CFG amplification) |
| `autoguidance_ratio` | How much autoguidance correction is applied during sampling |
| `caflow_noise_scale` | Noise injection strength during SDE backbone generation |
| `sampling_temp` | ProteinMPNN sequence diversity (see section 4.3) |

Rather than tuning these by hand, the pipeline uses **Bayesian Hyperparameter Optimization (HPO)** via Optuna to automatically search for parameter combinations that maximize the fraction of high-confidence immunoglobulin hits.

### 8.1 The Optimization Target

The objective metric is **`pct_target_fold_high_conf`** — the percentage of generated sequences that CATHe2 classifies as 2.60.40.x with prediction probability ≥ 0.7. This is evaluated **per protein length** (separately for 95, 100, 105, 110, and 115-residue chains), because the optimal generative parameters differ between lengths.

### 8.2 Tree-Structured Parzen Estimator (TPE)

Bayesian HPO works by building a **probabilistic surrogate model** of the objective function and using it to propose the next parameter set to try, rather than sampling blindly. Optuna uses the **Tree-Structured Parzen Estimator (TPE)** algorithm:

1. **Partition trials by quality** — after each trial, completed runs are split into "good" (*l(x)*) and "bad" (*g(x)*) groups based on a quantile threshold.
2. **Fit kernel density estimators** — separate KDEs are fitted over the good and bad parameter distributions.
3. **Sample where l(x)/g(x) is highest** — new parameter proposals are drawn from regions that are more likely under the good distribution than the bad one.
4. **Update and repeat** — after each new trial, the models are updated.

This concentrates sampling in promising regions of parameter space, converging on good configurations far faster than random or grid search.

### 8.3 Per-Length Studies

Each protein length gets its own independent Optuna study, persisted in a SQLite database (`optuna_hpo_len<N>.db`). Studies can be resumed across sessions and inspected with the Optuna dashboard. After optimization, the best parameters per length are written to `results/best_params_per_length.json` and used for the final large-scale run.

### 8.4 Warm-Start from Prior Experiments

Before running new trials, the optimizer is seeded with any existing results from `results/experiments.csv` via the `load_warmup` function. This **warm-start** lets Optuna build an initial surrogate model from hand-tuned or previously explored configurations, reducing the number of new pipeline runs needed to converge.


---

## 9. Pipeline Integration

The full pipeline operates in **three sequential stages**, orchestrated by a combination of Optuna (Bayesian HPO), Nextflow (main workflow), and standalone scripts (post-pipeline validation).

### Stage 1 — Hyperparameter Search (Optional)

Bayesian HPO tunes the four core generative parameters by running the full Nextflow pipeline ~40 times per target protein length and maximizing `pct_target_fold_high_conf`.

```
Optuna (TPE) ──► Nextflow pipeline run ──► read metric ──► update surrogate
                       (×40 trials)
```

Best parameters are saved to `results/best_params_per_length.json`.

### Stage 2 — Main Nextflow Pipeline

Using the best-found parameters, a final large-scale run generates and classifies candidates:

```
Proteina ──► ProteinMPNN ──► CATHe2 ──► GENERATE_REPORT ──► LOG_RUN
  (PDB)         (FASTA)       (CSV)        (HTML/CSV)         (JSON)
```

**Step 1 — GENERATE_BACKBONES (Proteina)**
Proteina generates backbone PDB files conditioned on CATH code `2.60.40.x` — the Ig-like β-sandwich fold. The backbones contain only Cα coordinates; no sequence is assigned yet.

**Step 2 — RUN_MPNN (ProteinMPNN)**
Each PDB backbone is passed individually to ProteinMPNN (in `--ca_only` mode). It generates 200 candidate amino acid sequences per backbone at temperature 0.925228, output as FASTA files. This step runs in parallel over all backbones (Nextflow flattens the PDB list into a stream).

**Step 3 — RUN_CATHE (CATHe2)**
All FASTA files are collected and merged into one batch. CATHe2 embeds each sequence with ProstT5, classifies it, and writes a `classifications.csv`. Sequences with CATHe2 prediction probability ≥ 0.7 for the 2.60.40 superfamily pass the primary filter.

**Step 4 — GENERATE_REPORT**
The report script filters to 2.60.40 hits, computes per-length statistics, generates a `report.html`, and writes `top_designs.csv` with the best candidates sorted by CATHe2 probability.

**Step 5 — LOG_RUN**
Run parameters and per-length metrics are appended to `results/experiments.csv` so Bayesian HPO can consume them in future optimization trials.

### Stage 3 — Post-Pipeline Structural Validation

The highest-confidence sequence candidates from Stage 2 are validated through a two-step structural pipeline:

```
top_designs.csv (CATHe2 ≥ 98%)
        ↓
    ESMFold ──► PDB structures
        ↓
    FoldSeek ──► structural search vs. CATH50
        ↓
  cross-reference CATHe2 + FoldSeek hits
        ↓
  best_200_validated_sequences.fasta
```

**Step 6 — ESMFold**
Top candidates (CATHe2 probability ≥ 98%) are folded into full-atom PDB structures. 

**Step 7 — FoldSeek**
ESMFold-predicted structures are searched against the CATH50 database. FoldSeek encodes each structure as a 3Di string and performs fast structure-to-structure alignment, returning the closest CATH-labeled hits for each designed sequence.

**Step 8 — Final Validation**
`final_validation.py` cross-references CATHe2 labels (sequence-based) with FoldSeek CATH hits (structure-based). Sequences confirmed by both channels — CATHe2 predicts 2.60.40.x and FoldSeek finds a 2.60.40.x structural match — are ranked and the top 200 are written to `best_200_validated_sequences.fasta`.

