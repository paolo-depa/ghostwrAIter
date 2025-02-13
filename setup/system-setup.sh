#!/bin/bash
CDI_DIR_PATH="/etc/cdi"
CDI_FILE_PATH="$CDI_DIR_PATH/nvidia.yaml"

if [[ -f "$(dirname "$0")/system-setup.env" ]]; then
    source "$(dirname "$0")/system-setup.env"
elif [[ -f "$HOME/.config/ghostwraiter/system-setup.env" ]]; then
    source "$HOME/.config/ghostwraiter/system-setup.env" 
else
    echo "system-setup.env file not found."
    exit 1
fi

if ! sudo SUSEConnect -l | grep -q "Containers Module" | grep -q "Activated"; then
    sudo SUSEConnect --product sle-module-containers/15.5/x86_64
fi

if ! command -v podman &> /dev/null; then
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
PODMAN_GPU_PARAM=''
# run Ollama container
PODMAN_GPU_PARAM=''
if [[ $ENABLE_GPU != 'false' ]]; then

    # Testing if nvidia container toolkit was installed
    sudo which nvidia-ctk >> /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
            echo "nvidia-ctk not found : please follow the docs at https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html"
            exit -1
    fi

    if [[ ! -d $CDI_DIR_PATH ]]; then
        sudo mkdir $CDI_DIR_PATH
    fi

    if [[ ! -f $CDI_FILE_PATH ]]; then
        sudo nvidia-ctk cdi generate --output=$CDI_FILE_PATH
    fi

    GPU_NAME="nvidia.com/gpu=$ENABLE_GPU"
    if sudo nvidia-ctk cdi list 2>> /dev/null | grep -q $GPU_NAME; then
        PODMAN_GPU_PARAM="--device $GPU_NAME"
    else
        echo "$GPU_NAME not found"
    fi

fi

 podman run -d $PODMAN_GPU_PARAM -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

for model in ${OLLAMA_MODELS//,/ }
do
    podman exec ollama ollama run $model
done

for embedding in ${OLLAMA_EMBEDDINGS//,/ }
do
    podman exec ollama ollama pull $embedding
done

# (Optional) Start an OpenwebUI instance free of auth
# podman run -d -p 3000:8080 -e WEBUI_AUTH=False -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
