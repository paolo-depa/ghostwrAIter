#!/bin/bash

# Source the environment variables
if [[ -f "$(dirname "$0")/cli-setup.env" ]]; then
    source $(dirname "$0")/cli-setup.env
elif [[ -f "$HOME/.config/ghostwraiter/cli-setup.env" ]]; then
    source "$HOME/.config/ghostwraiter/cli-setup.env"
else
    echo "cli-setup.env file not found."
    exit 1
fi

# Install the libraries listed in PIP_LIBS
# Check for Python version >= 3.11
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
    echo "Python 3.11 or higher is required. Please update your Python version."
    exit 1
fi

# Check for pip
if ! command -v pip &> /dev/null; then
    echo "pip could not be found. Please install pip."
    exit 1
fi

pip install $PIP_LIBS

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "export PATH=\"~/.local/bin:\$PATH\"" >> ~/.bashrc
fi

if [[ -n "$PYTHONPATH" ]]; then
    if [[ "$PYTHONPATH" != *".local/lib/python3.11/site-packages"* ]]; then
        echo "export PYTHONPATH=\"~/.local/lib/python3.11/site-packages:$PYTHONPATH\"" >> ~/.bashrc
    fi
else
    echo "export PYTHONPATH=\"~/.local/lib/python3.11/site-packages\"" >> ~/.bashrc
fi
