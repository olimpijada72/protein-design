# compute_metrics.py
import pandas as pd
import json
from pathlib import Path

def compute_metrics(csv_path, target_fold="2.60.40"):
    """
    Compute metrics from sequences CSV
    """

    df = pd.read_csv(csv_path)
    df["sequence_length"] = df["Sequence"].str.len()
    
    
    # Overall metrics
    total = len(df)
    target_fold_count = (df['CATHe_Predicted_SFAM'].str.startswith(target_fold)).sum()
    target_fold_high_conf = (
        (df['CATHe_Predicted_SFAM'].str.startswith(target_fold)) & 
        (df['CATHe_Prediction_Probability'] > 0.7)
    ).sum()
    
    df_2_60_40 = df[df['CATHe_Predicted_SFAM'].str.startswith(target_fold)]

    metrics = {
        'overall': {
            'target_fold_count': int(target_fold_count),
            'pct_target_fold': round(100 * target_fold_count / total, 2),
            'pct_target_fold_high_conf': round(100 * target_fold_high_conf / total, 2),
            'mean_probability': round(df_2_60_40['CATHe_Prediction_Probability'].mean(), 4),
            'median_probability': round(df_2_60_40['CATHe_Prediction_Probability'].median(), 4),
        },
        'per_length': {}
    }
    
    # Per-length stratification
    for length in sorted(df['sequence_length'].unique()):
        df_len = df[df['sequence_length'] == length]
        df_len_2_60_40 = df_len[df_len['CATHe_Predicted_SFAM'].str.startswith(target_fold)]
        n = len(df_len)
        target_fold_n = (df_len['CATHe_Predicted_SFAM'].str.startswith(target_fold)).sum()
        target_fold_hc_n = (
            (df_len['CATHe_Predicted_SFAM'].str.startswith(target_fold)) & 
            (df_len['CATHe_Prediction_Probability'] > 0.7)
        ).sum()
        
        metrics['per_length'][int(length)] = {
            'target_fold_count': int(target_fold_n),
            'pct_target_fold': round(100 * target_fold_n / n, 2) if n > 0 else 0,
            'pct_target_fold_high_conf': round(100 * int(target_fold_hc_n) / n, 2) if n > 0 else 0,
            'mean_probability': round(df_len_2_60_40['CATHe_Prediction_Probability'].mean(), 4),
            'median_probability': round(df_len_2_60_40['CATHe_Prediction_Probability'].median(), 4),

        }
    
    return metrics

if __name__ == '__main__':
    import sys
    csv_path = sys.argv[1]
    metrics = compute_metrics(csv_path)
    print(json.dumps(metrics, indent=2))