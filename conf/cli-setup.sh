#!/bin/bash

# Source the environment variables
source /home/ppasquale/git/ghostwrAIter/conf/cli-setup.env

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
