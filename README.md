# protein-design

This project performs *in silico* design of the **immunoglobulin** protein, known in CATH notation as **2.60.40.x**. The pipeline outputs amino acid sequences of the immunoglobulin fold. Immunoglobulins are central to the immune system, and computationally designed variants can aid in the discovery of new therapeutics.

## How to setup 
This project was developed on a MacBook Pro (M1 Pro, 32GB RAM) and has not been tested on other operating systems or hardware configurations. Some adaptation may be required on non-Mac systems.

This pipeline depends on several large-scale bioinformatics tools developed by different teams, each requiring its own virtual environment. All environments can be created automatically by running `setup_envs.sh`. conda is required.

```
chmod +x setup_envs.sh
bash setup_envs.sh
```

After setting up the environments, activate the main one:

```
conda activate protein_design_env
```

Then download all model weights:

```
python download_large_files.py   
```

## How to Run Pipeline
The pipeline is orchestrated using [Nextflow](https://www.nextflow.io/docs/latest/index.html).

Navigate to the pipeline directory:
```
cd pipeline
```

Run the pipeline:
```
nextflow run local_pipeline.nf -with-conda
```

If the pipeline fails, it can be resumed from the point of failure using the `-resume` flag:

```
nextflow run local_pipeline.nf -with-conda -resume
```


## Project Organization

## Explination of the Theory



## Detailed Technical Explination 


## Guide on Contributing

