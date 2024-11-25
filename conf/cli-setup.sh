#!/bin/bash

# Source the environment variables
if [[ -f "$(dirname "$0")/cli-setup.env" ]]; then
    source ~/.config/ghostwraiter/cli-setup.env
elif [[ -f ~/.config/ghostwraiter/cli-setup.env ]]; then
    source "$(dirname "$0")/cli-setup.env"
else
    echo "cli-setup.env file not found."
    exit 1
fi

# Install the libraries listed in PIP_LIBS
pip install $PIP_LIBS

if [[ ":$PATH:" != *":.local/bin:"* ]]; then
    echo "export PATH=\"~/.local/bin:\$PATH\"" >> ~/.bashrc
fi

if [[ -n "$PYTHONPATH" ]]; then
    if [[ "$PYTHONPATH" != *".local/lib/python3.11/site-packages"* ]]; then
        echo "export PYTHONPATH=\"~/.local/lib/python3.11/site-packages:$PYTHONPATH\"" >> ~/.bashrc
    fi
else
    echo "export PYTHONPATH=\"~/.local/lib/python3.11/site-packages\"" >> ~/.bashrc
fi
