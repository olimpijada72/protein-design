#!/usr/bin/env python3
"""
Downloads pipeline results from HuggingFace and extracts them to results/.
Run from the repo root: python download_results.py

Requires: pip install huggingface_hub
"""

import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "olimpijada72/protein-design"
REPO_TYPE = "model"

FILENAME = "results.zip"
DEST = "results"

REPO_ROOT = Path(__file__).parent


def download_and_extract(filename: str, dest_rel: str) -> None:
    dest = REPO_ROOT / dest_rel
    dest.mkdir(parents=True, exist_ok=True)

    print(f"\n[{filename}] Downloading...")
    local_zip = hf_hub_download(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        filename=filename,
        local_dir=str(REPO_ROOT / ".hf_cache"),
    )

    print(f"[{filename}] Extracting to {dest_rel}/")
    with zipfile.ZipFile(local_zip, "r") as zf:
        zf.extractall(dest)

    print(f"[{filename}] Done.")


def main() -> None:
    download_and_extract(FILENAME, DEST)
    print("\nResults downloaded and extracted successfully.")


if __name__ == "__main__":
    main()
