import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import Levenshtein
import re
import numpy as np
import argparse
import base64
from io import BytesIO
import webbrowser
import os

def generate_report(csv_path):
    df = pd.read_csv(csv_path)

    # Filter for the 2.60.40 superfamily
    df_26040 = df[df["CATHe_Predicted_SFAM"].str.contains("2.60.40")].copy()

    # Sequence length
    df_26040["seq_len"] = df_26040["Sequence"].str.len()

    # Extract metrics from Record column
    def extract_temp(record):
        match = re.search(r"T=([0-9.]+)", str(record))
        return float(match.group(1)) if match else np.nan

    def extract_global_score(record):
        match = re.search(r"global_score=([0-9.\-]+)", str(record))
        return float(match.group(1)) if match else np.nan

    def extract_seq_recovery(record):
        match = re.search(r"seq_recovery=([0-9.\-]+)", str(record))
        return float(match.group(1)) if match else np.nan

    df_26040["temperature"] = df_26040["Record"].apply(extract_temp)
    df_26040["global_score"] = df_26040["Record"].apply(extract_global_score)
    df_26040["seq_recovery"] = df_26040["Record"].apply(extract_seq_recovery)

    # Aggregate stats
    len_stats = df_26040.groupby("seq_len").agg(
        count=("CATHe_Prediction_Probability", "count"),
        mean_prob=("CATHe_Prediction_Probability", "mean"),
    ).reset_index()

    temp_stats = df_26040.groupby("temperature").agg(
        count=("CATHe_Prediction_Probability", "count"),
        mean_prob=("CATHe_Prediction_Probability", "mean"),
    ).reset_index()

    # Diversity Plot
    sequences = df_26040['Sequence'].tolist() # Fixed: Was 'sequence', now 'Sequence'
    subset = sequences[:50] 
    n = len(subset)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist = Levenshtein.distance(subset[i], subset[j]) / max(len(subset[i]), len(subset[j]))
            dist_matrix[i, j] = dist_matrix[j, i] = dist

    plt.figure(figsize=(8, 6))
    sns.heatmap(dist_matrix, cmap="viridis")
    plt.title('Sequence Diversity (Normalized Edit Distance)')
    
    tmpfile = BytesIO()
    plt.savefig(tmpfile, format='png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    plt.close()

    # Generate HTML
    cols_to_show = ["Sequence", "CATHe_Prediction_Probability", "CATHe_Predicted_SFAM", "seq_len", "temperature", "global_score", "seq_recovery"]
    df_26040 = df_26040[cols_to_show].sort_values("CATHe_Prediction_Probability", ascending=False)
    final_table = df_26040.to_html(index=False)

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Protein Design Report: 2.60.40 Superfamily</h1>
        <h2>Length Distribution (Top 10)</h2>
        {len_stats.sort_values("count", ascending=False).head(10).to_html(index=False)}
        
        <h2>Temperature Distribution (Top 10)</h2>
        {temp_stats.sort_values("count", ascending=False).head(10).to_html(index=False)}
        
        <h2>Diversity Analysis</h2>
        <img src='data:image/png;base64,{encoded}'>
        
        <h2>Top Designs (Ordered by CATHe Probability)</h2>
        {final_table}
    </body>
    </html>
    """

    with open("report.html", "w") as f:
        f.write(html_content)
    print(f"Report successfully saved as report.html")

    df_26040.to_csv("top_designs.csv", index=False)

    abs_path = os.path.abspath("report.html")
    webbrowser.open(f'file://{abs_path}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    generate_report(args.input)