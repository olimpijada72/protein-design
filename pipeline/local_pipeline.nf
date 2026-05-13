nextflow.enable.dsl=2

// --- 1. GLOBAL PARAMETERS ---
// Uses the parent of the directory where this script sits
params.project_root = "${workflow.projectDir.parent}"

// Environment Paths
params.proteina_env = "/opt/miniconda3/envs/proteina_env" 
params.cathe_venv   = "${params.project_root}/external/CATHe2/venv_2"

// Script Paths
params.proteina_script = "${params.project_root}/external/proteina/script_utils/inference_cond_sampling.py"
params.mpnn_script     = "${params.project_root}/external/proteina/ProteinMPNN/protein_mpnn_run.py"
params.cathe_script    = "${params.project_root}/external/CATHe2/src/cathe-predict/cathe_predictions.py"


// --- 2. PROCESSES ---

process GENERATE_BACKBONES {
    conda "${params.proteina_env}"
    
    output:
    path "backbones/*.pdb", emit: pdbs

    script:
    """
    mkdir -p backbones

    # 1. Run the script with clear argument spacing
    python ${params.proteina_script} \
        --config_name inference_cond_autoguidance \
        --cath_codes 2.60.40.x \
        --nsamples 3 
    
    # 2. Use DOUBLE backslash for the semicolon so Nextflow doesn't swallow the arguments
    find . -name "*.pdb" -not -path "./backbones/*" -exec mv {} backbones/ \\;
    """
}

process RUN_MPNN {
    conda "${params.proteina_env}"
    // Note: I removed publishDir here to avoid clutter, 
    // but you can keep it if you want to see the FASTA files.

    input:
    path pdb

    output:
    // Change this to look inside the seqs subfolder
    path "seqs/*.fa", emit: fastas

    script:
    """
    python ${params.mpnn_script} \
        --ca_only \
        --pdb_path "${pdb}" \
        --out_folder ./ \
        --num_seq_per_target 50 \
        --sampling_temp "0.3"
    """
}
process RUN_CATHE {
    cache false
    publishDir "final_results", mode: 'copy'
    // Ensure we are using the venv for the python execution
    beforeScript "source ${params.cathe_venv}/bin/activate"

    input:
    path fastas, stageAs: 'collected_fastas/*.fa'

    output:
    path "classifications.csv"

    script:
    """
    # 1. Merge all input fastas into one file in the CURRENT work dir
    cat collected_fastas/*.fa > merged.fasta
    
    # 2. Get the full path of our new merged file
    MERGED_PATH=\$(readlink -f merged.fasta)
    OUT_DIR=\$(pwd)
    CATHE_ROOT="${params.project_root}/external/CATHe2"

    # 3. Move into the CATHe directory and overwrite the target file
    cd "\$CATHE_ROOT"
    
    # Use -f (force) to overwrite and -p to preserve if needed
    cp -f "\$MERGED_PATH" src/cathe-predict/sequences.fasta

    echo "Verified: sequences.fasta is now updated from \$MERGED_PATH"

    # 4. Run the prediction
    python src/cathe-predict/cathe_predictions.py --model ProstT5 --input_type AA

    # 5. Find the result and bring it back to the Nextflow work dir
    CSV=\$(find . -maxdepth 4 -type f -name "Results.csv" | head -n 1)
    if [ -z "\$CSV" ]; then
        echo "ERROR: Results.csv not found."
        exit 1
    fi

    cp "\$CSV" "\$OUT_DIR/classifications.csv"
    """
}

// --- 3. WORKFLOW ---

workflow {
    backbones_ch = GENERATE_BACKBONES()
    
    // Flatten turns the list of PDBs into a stream of individual files
    pdb_ch = backbones_ch.pdbs.flatten()

    // Pass the channel itself, not .pdbs
    fastas_ch = RUN_MPNN(pdb_ch)

    // Collect all FASTAs into one list so CATHe runs ONCE on the whole batch
    RUN_CATHE(fastas_ch.fastas.collect())
}