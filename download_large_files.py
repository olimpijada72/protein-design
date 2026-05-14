#!/usr/bin/env python3
"""
Downloads large files from HuggingFace and extracts them to the correct locations.
Run from the repo root: python download_large_files.py
Requires: pip install huggingface_hub
"""

import os
import shutil
import stat
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "olimpijada72/protein-design"
REPO_TYPE = "model"

# (zip filename, extract destination relative to repo root)
FILES = [
    ("ProteinMPNN.zip",                    "external/proteina"),
    ("openfold.zip",                        "external/proteina"),
    ("proteina_training_data_indices.zip",  "external/proteina"),
    ("data.zip",                            "external/proteina"),
    ("saved_models.zip",                    "external/CATHe2"),
    ("cathe-predict.zip",                   "external/CATHe2/src"),
    ("foldseek.zip",                        "external/CATHe2"),
]

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
    for filename, dest_rel in FILES:
        download_and_extract(filename, dest_rel)

    # foldseek binary needs execute permission
    foldseek_bin = REPO_ROOT / "external/CATHe2/foldseek/bin/foldseek"
    if foldseek_bin.exists():
        foldseek_bin.chmod(foldseek_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print("\nSet foldseek as executable.")

    for macosx_dir in (REPO_ROOT / "external").rglob("__MACOSX"):
        shutil.rmtree(macosx_dir)
    print("\nCleaned up __MACOSX directories.")

    print("\nAll files downloaded and extracted successfully.")


if __name__ == "__main__":
    main()
