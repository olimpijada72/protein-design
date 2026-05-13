#!/bin/bash

echo "venv_1 Pre requirement set up"

# Install Python 3.9 using Homebrew
# NOTE: /usr/local is typical for Intel Macs; /opt/homebrew is typical for Apple Silicon (M-series) Macs
brew install python@3.9

# Create a virtual environment and activate it
PYTHON_BIN=$(brew --prefix python@3.9)/bin/python3.9
$PYTHON_BIN -m venv venv_1
source venv_1/bin/activate

# Upgrade pip and install setuptools
pip install --upgrade pip
pip install setuptools==69.5.1

# Install gensim and bio-embeddings
pip install gensim==4.3.2
pip install git+https://github.com/sacdallago/bio_embeddings.git@develop

# Install system packages
# Replaces multiple apt-get installs for blas/lapack/gfortran libs
brew install openblas liblapack libblas gfortran

# Install additional Python packages
pip install wheel lazr.uri

# Set torch path (optional, check if needed)
# export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])')

# Modify gensim matutils.y
sed -i '' 's/from scipy.linalg import get_blas_funcs, triu/from scipy.linalg import get_blas_funcs\nfrom numpy import triu/' ./venv_1/lib/python3.9/site-packages/gensim/matutils.py

# CUDA/Driver installations are commented out as they are Linux-specific
# ... (NVIDIA driver/CUDA blocks removed for brevity, they are commented out in original)

# Deactivate and reactivate the virtual environment
deactivate
source venv_1/bin/activate

# Install Python requirements
echo "Installing Python requirements for venv_1, this may take a while..."
pip install -r requirements.txt

# Install MMseqs2 using Homebrew
echo "Installing MMseqs2..."
brew install mmseqs2

# Install Foldseek
echo "Installing Foldseek..."
wget https://mmseqs.com/foldseek/foldseek-linux-avx2.tar.gz
tar xvzf foldseek-linux-avx2.tar.gz
rm foldseek-linux-avx2.tar.gz