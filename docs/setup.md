# Setup & Usage Guide

This project was developed on a MacBook Pro (M1 Pro, 32GB RAM) and has not been tested on other operating systems or hardware configurations. Some adaptation may be required on non-Mac systems.

## 1. Environment Setup

This pipeline depends on several large-scale bioinformatics tools developed by different teams, each requiring its own virtual environment. All environments can be created automatically by running `setup_envs.sh`. conda is required.

```bash
chmod +x setup_envs.sh
bash setup_envs.sh
```

During setup you will be prompted to enter the path to the Proteina data directory for a `.env` file. Enter:

```
path_to_your_project/protein-design/external/proteina/data
```

After setup, activate the main environment:

```bash
conda activate protein_design_env
```

Then download all model weights:

```bash
python download_large_files.py
```

---

## 2. Single Pipeline Run

The pipeline is orchestrated using [Nextflow](https://www.nextflow.io/docs/latest/index.html). Navigate to the pipeline directory and run:

```bash
cd pipeline
nextflow run main.nf -with-conda
```

If the pipeline fails mid-run, resume from the point of failure with:

```bash
nextflow run main.nf -with-conda -resume
```

**What this produces:**
- `results/artifacts/<run_id>/top_designs.csv` — sequences classified as 2.60.40.x with CATHe2 probability ≥ 70%
- `results/artifacts/<run_id>/report.html` — per-length statistics and diversity plots
- `results/experiments.csv` — run parameters and metrics appended for every completed run

---

## 3. Bayesian Hyperparameter Optimization (Optional)

HPO tunes the four core generative parameters (`guidance_weight`, `autoguidance_ratio`, `caflow_noise_scale`, `sampling_temp`) by running the full pipeline repeatedly and maximizing the fraction of high-confidence immunoglobulin hits. Run from the project root, specifying one protein length at a time:

```bash
python src/bayes_opt.py --nres-lens 95
python src/bayes_opt.py --nres-lens 100
python src/bayes_opt.py --nres-lens 105
```

Optional flags:

```bash
--n-trials 60        # number of trials to run (default: 40)
--study-name my_exp  # override the auto-generated study name
--no-warmup          # skip seeding from prior experiments.csv rows
```

Each trial runs the full Nextflow pipeline (~20 min) and logs results to `results/experiments.csv`. After all trials complete, the best parameters per length are saved to `results/best_params_per_length.json`.

To inspect the optimization history interactively:

```bash
optuna-dashboard sqlite:///results/optuna_hpo_len95.db
```

---

## 4. Compile Designs Across Runs

After running the pipeline one or more times (either standalone or via HPO), concatenate all `top_designs.csv` files into a single file and filter to the highest-confidence candidates (CATHe2 probability ≥ 98%):

```bash
python src/concat_designs.py
```

This reads every `results/artifacts/*/top_designs.csv`, deduplicates by sequence, and produces:

- `results/all_designs.csv` — all unique sequences across all runs
- `results/best_designs.csv` — sequences with CATHe2 probability > 98%
- `results/best_designs.fasta` — same sequences in FASTA format, used as input for ESMFold

---

## 5. ESMFold Structure Prediction

ESMFold runs in Google Colab because it requires a GPU and significant RAM not available locally.

1. Open the ESMFold notebook in [Google Colab](https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/ESMFold.ipynb)
2. Paste the contents of `results/best_designs.fasta` into the sequence input field
3. Run the notebook — it will fold each sequence and generate a PDB file per sequence
4. Download the resulting `.pdb` files to your local machine

---

## 6. FoldSeek Structural Search

Move the downloaded PDB files into the FoldSeek input directory:

```bash
mv /path/to/downloaded/pdbs/*.pdb results/foldseek/esmfold_best_designs/
```

Then run the search script from the project root:

```bash
bash src/run_foldseek.sh
```

This will:
1. Download the CATH50 database on first run (skipped automatically on subsequent runs)
2. Build a FoldSeek database from the PDB files
3. Search against CATH50
4. Write results to `results/foldseek/foldseek_results.txt`

---

## 7. Final Validation

Cross-reference CATHe2 sequence classifications with FoldSeek structural hits to produce the final validated candidate set:

```bash
python src/final_validation.py
```

This produces:
- `results/best_200_validated_sequences.fasta` — top 200 sequences confirmed by both CATHe2 and FoldSeek as immunoglobulin-like
- `results/best_200_validated_sequences.txt` — same sequences as plain text

A summary is printed to stdout showing total sequences checked, exact CATH matches, and broad 2.60.40.x hits.

---

## Downloading Pre-computed Results

If you want to skip the pipeline and inspect the results from the runs already conducted, you can download them directly from HuggingFace:

```bash
python download_results.py
```

This downloads and extracts `results.zip` from `olimpijada72/protein-design` into the `results/` directory, giving you the full `experiments.csv`, `best_designs.csv`, `foldseek_results.txt`, and final validated sequences without running any pipeline steps.

Requires the `huggingface_hub` package (`pip install huggingface_hub`).

---

## Full Workflow Summary

```
[optional] python src/bayes_opt.py --nres-lens <N>   # tune parameters
                    ↓
cd pipeline && nextflow run main.nf -with-conda       # generate & classify
                    ↓
python src/concat_designs.py                          # compile best designs
                    ↓
ESMFold (Google Colab) → download .pdb files          # fold structures
                    ↓
bash src/run_foldseek.sh                              # structural search
                    ↓
python src/final_validation.py                        # cross-validate & export
```

