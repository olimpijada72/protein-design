
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
        --nsamples ${params.proteina.nsamples} \
        seed=${params.proteina.seed} \
        dt=${params.proteina.dt} \
        guidance_weight=${params.proteina.guidance_weight} \
        autoguidance_ratio=${params.proteina.autoguidance_ratio} \
        sampling_caflow.sampling_mode=${params.proteina.sampling_mode} \
        sampling_caflow.sc_scale_noise=${params.proteina.caflow_noise_scale} \
        nres_lens=[${params.proteina.nres_lens.join(',')}]

    
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
        --num_seq_per_target ${params.mpnn.num_seq_per_target} \
        --sampling_temp "${params.mpnn.sampling_temp}"
    """
}

process RUN_CATHE {
    publishDir "final_results", mode: 'copy'
    beforeScript "source ${params.cathe_venv}/bin/activate"

    input:
    path fastas // No need for stageAs here if we handle them directly

    output:
    path "classifications.csv"

    script:
    """
    # Merge all provided fasta files directly
    cat *.fa > merged.fasta
    
    MERGED_PATH=\$(readlink -f merged.fasta)
    OUT_DIR=\$(pwd)
    CATHE_ROOT="${params.project_root}/external/CATHe2"

    # Move into the CATHe directory
    cd "\$CATHE_ROOT"
    
    # Overwrite the target file
    cp -f "\$MERGED_PATH" src/cathe-predict/sequences.fasta

    # Run the prediction
    python src/cathe-predict/cathe_predictions.py --model ProstT5 --input_type AA

    # Check for results
    CSV=\$(find . -maxdepth 4 -type f -name "Results.csv" | head -n 1)
    if [ -z "\$CSV" ]; then
        echo "ERROR: Results.csv not found."
        exit 1
    fi

    cp "\$CSV" "\$OUT_DIR/classifications.csv"
    """
}

process GENERATE_REPORT {
    conda "${params.protein_design_env}"
    publishDir "final_results", mode: 'copy'

    input:
    path csv_file

    output:
    path "report.html", emit: html
    path "top_designs.csv", emit: csv

    script:
    """
    python ${params.project_root}/src/generate_report.py --input ${csv_file}
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
    cathe_results_ch = RUN_CATHE(fastas_ch.fastas.collect())

    GENERATE_REPORT(cathe_results_ch)
}