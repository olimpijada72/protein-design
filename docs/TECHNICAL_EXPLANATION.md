# Explanation of Technical Aspects 

Here I will explain how each of these sub-projects are used and setup, and how Nextflow connects all of it. I will also explain how to use nextflow

## How proteina Works?
Explain what this is and the reasoning behind it
```
python /inference_cond_sampling.py \
    --config_name inference_cond_autoguidance \
    --cath_codes 2.60.40.x \
    --nsamples 1 

```

Explain this config and the reasoning behind it
```
defaults:
  - inference_base
  - _self_

run_name_: cond_autoguidance
ckpt_name: proteina_v1.4_D21M_400M_tri.ckpt
autoguidance_ckpt_path: "/Users/mipopovic/Desktop/proteina/data/checkpoints/proteina_v1.8_D21M_400M_tri_autoguidance.ckpt"

self_cond: True
fold_cond: True
cath_code_level: "T"  # Guidance level

guidance_weight: 2.0

sampling_caflow:
  sampling_mode: sc  # "vf" for ODE sampling, "sc" for SDE sampling. "vf" does not allow low temperature sampling.
  sc_scale_noise: 0.3  # noise scale, used if sampling_mode == "sc"
```

## How ProteinMPNN Works?
```
python ${params.mpnn_script} \
    --ca_only \
    --pdb_path "${pdb}" \
    --out_folder ./ \
    --num_seq_per_target 50 \
    --sampling_temp "0.3"
```
## How CATHe2 Works?

```
python src/cathe-predict/cathe_predictions.py --model ProstT5 --input_type AA
```

## How Nextflow Ties this All Together?
