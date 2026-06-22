#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FOLDSEEK_DIR="$PROJECT_ROOT/results/foldseek"


cd "$FOLDSEEK_DIR"

# Download CATH50 database only if not already present
if [ ! -f "cath_db.dbtype" ]; then
    foldseek databases CATH50 cath_db tmp
fi

foldseek createdb esmfold_best_designs query_db
foldseek search query_db cath_db results tmp
foldseek convertalis query_db cath_db results foldseek_results.txt --format-mode 0
