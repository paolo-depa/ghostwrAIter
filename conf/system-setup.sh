#!/bin/bash
source ./system-setup.env

if ! sudo SUSEConnect -l | grep -q "Containers Module 15 SP5 x86_64 (Activated)"; then
    sudo SUSEConnect --product sle-module-containers/15.5/x86_64
fi

if ! command -v podman &> /dev/null
then
    sudo zypper in -y podman
fi

if systemctl is-active --quiet firewalld; then
    if ! sudo firewall-cmd --list-ports | grep -q "3000/tcp"; then
        sudo firewall-cmd --add-port=3000/tcp --zone=public --permanent
    fi
    if ! sudo firewall-cmd --list-ports | grep -q "11434/tcp"; then
        sudo firewall-cmd --add-port=11434/tcp --zone=public --permanent
    fi
    sudo firewall-cmd --reload
fi

# run Ollama container
podman run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

for model in ${OLLAMA_MODELS//,/ }
do
    podman exec ollama ollama run $model
done
for embedding in ${OLLAMA_EMBEDDINGS//,/ }
do
    podman exec ollama ollama pull $embedding
done

# Start an OpenwebUI instance free of auth
podman run -d -p 3000:8080 -e WEBUI_AUTH=False -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
