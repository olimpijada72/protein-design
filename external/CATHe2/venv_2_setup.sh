#!/bin/bash

echo "venv_2 Pre requirement set up"

# Install Python 3.9 using Homebrew
# NOTE: /usr/local is typical for Intel Macs; /opt/homebrew is typical for Apple Silicon (M-series) Macs
brew install python@3.9

# Create a new virtual environment and activate it
# Use the Homebrew-installed python path
PYTHON_BIN=$(brew --prefix python@3.9)/bin/python3.9
$PYTHON_BIN -m venv venv_2
source venv_2/bin/activate

# Upgrade pip and install setuptools
pip install --upgrade pip
pip install setuptools==69.5.1

# Install manually gensim, wheel and lazr.uri
pip install gensim==4.3.2
pip install wheel lazr.uri

# Install required system packages for scientific computing via Homebrew
# Replaces multiple apt-get installs for blas/lapack/gfortran libs
brew install openblas liblapack libblas gfortran

# Install PyTorch and its dependencies with CUDA 11.8 support
# Note: PyTorch will fall back to CPU if no compatible NVIDIA/CUDA setup is found on Mac
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Set the PyTorch path (optional, keeping commented out)
# export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])')

# Modify gensim matutils.y
sed -i '' 's/from scipy.linalg import get_blas_funcs, triu/from scipy.linalg import get_blas_funcs\nfrom numpy import triu/' ./venv_2/lib/python3.9/site-packages/gensim/matutils.py

# CUDA/Driver installations are commented out as they are Linux-specific
# ... (NVIDIA driver/CUDA blocks removed for brevity, they are commented out in original)

# Deactivate and reactivate the virtual environment
deactivate
source venv_2/bin/activate

# Install requirements from requirements_2.txt
echo "Installing Python requirements from requirements_2.txt, this may take a while..."
pip install -r requirements_2.txt

# Install MMseqs2 using Homebrew
echo "Installing MMseqs2..."
brew install mmseqs2

# Install foldseek
echo "Installing foldseek..."
wget https://mmseqs.com/foldseek/foldseek-linux-avx2.tar.gz
tar xvzf foldseek-linux-avx2.tar.gz
rm foldseek-linux-avx2.tar.gz

echo 'export PATH=$(pwd)/foldseek/bin/:$PATH' >> ./venv_2/bin/activate