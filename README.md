# Immunoglobulin Protein Design Pipeline
![Python](https://img.shields.io/badge/python-3.11-blue)
![Nextflow](https://img.shields.io/badge/orchestrator-nextflow-green)
![License](https://img.shields.io/badge/license-MIT-purple)


Generative protein design pipeline for immunoglobulin backbone synthesis and fold validation using flow-based models and graph neural networks.

![protein_rotating](figures/proteins_rotating.gif)

## Overview


Designing novel proteins computationally remains one of the central challenges in modern bioinformatics and generative machine learning. This project implements an end-to-end protein design pipeline focused on immunoglobulin-like folds (CATH 2.60.40.x), integrating generative backbone synthesis, sequence design, and fold-level structural validation into a unified reproducible workflow.

For a detailed explination of the theoretical apsects of the project, consult the document at `docs/THEORY_EXPLANATION.md`, and a precise technical breakdown can be found at `docs/TECHNICAL_EXPLANATION.md`.



![Immunoglobulin_image](figures/Immunoglobulin_image.jpg)


## Architecture

![architecture](figures/protein-design_architecture.png)

The pipeline works as follows:
- **Proteina** generates plausible α-carbon backbone geometries using flow-based generative modeling.
- **ProteinMPNN** designs amino acid sequences conditioned on the generated backbone structure.
- **CATHe2** predicts the resulting structural fold family to filter candidates belonging to the immunoglobulin-like β-sandwich architecture.
## Key Features

- End-to-end automated protein generation pipeline
- Flow-based backbone synthesis using Proteina
- Sequence generation with ProteinMPNN
- Structural fold validation using CATHe2
- Reproducible orchestration with Nextflow
- Modular multi-environment setup

## Results

Example outputs/images



## Installation
For a detailed explanation on how to setup the project, consult this guide `docs/SETUP.md`. The basic commands are the following:

```
chmod +x setup_envs.sh
bash setup_envs.sh
```
```
conda activate protein_design_env
```
```
python download_large_files.py   
```


## Usage
For a detailed explanation on how to run the project, consult this guide `docs/SETUP.md`. The basic commands are the following:
```
cd pipeline
nextflow run local_pipeline.nf -with-conda

```

## Repository Structure

The repository integrates external state-of-the-art protein generation ([proteina](https://github.com/NVIDIA-Digital-Bio/proteina/)) and classification frameworks ([CATHe2](https://github.com/Mouret-Orfeu/CATHe2)) into a unified reproducible pipeline.
```
.
├── download_large_files.py
├── environment.yaml
├── external
│   ├── CATHe2
│   └── proteina
├── LICENSE
├── pipeline
│   ├── final_results
│   ├── local_pipeline.nf
│   └── work
├── README.md
└── setup_envs.sh
```



## My Contributions
- Designed and implemented an end-to-end protein design pipeline
- Integrated multiple state-of-the-art protein ML models
- Built reproducible multi-environment infrastructure
- Automated orchestration using Nextflow
- Developed filtering and evaluation workflow for immunoglobulin fold candidates

## Future Work

- Structural validation using AlphaFold2/ESMFold
- Energy minimization and stability estimation
- Reinforcement learning for fold optimization
- Interactive visualization dashboard
- Fine-tuning backbone generators on immunoglobulin datasets
## References

Papers/repos