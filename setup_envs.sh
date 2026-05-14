#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
conda env create -f environment.yaml

# ── CATHe2 venv ─────────────────────────────────────────────────────────────
echo "==> Setting up CATHe2 virtual environment..."
cd "$REPO_ROOT/external/CATHe2"
bash venv_2_setup.sh
cd "$REPO_ROOT"
echo "==> CATHe2 venv done."

# ── proteina conda env ───────────────────────────────────────────────────────
echo "==> Setting up proteina conda environment..."
cd "$REPO_ROOT/external/proteina"

conda env create -f environment.yaml

# conda activate doesn't work in non-interactive shells; use `conda run` instead
conda run -n proteina_env pip install -e .

cd "$REPO_ROOT"
echo "==> proteina env done."

# ── .env file ────────────────────────────────────────────────────────────────
ENV_FILE="$REPO_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "==> Creating .env file..."
    read -r -p "Enter the path where you store data files (DATA_PATH): " data_path
    echo "DATA_PATH=$data_path" > "$ENV_FILE"
    echo "==> .env created at $ENV_FILE"
else
    echo "==> .env already exists, skipping."
fi

echo ""
echo "Setup complete."
echo "To activate the proteina environment: conda activate proteina_env"
