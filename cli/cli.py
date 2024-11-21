import os
import json
import argparse
import ollama

# Define the path for the settings file
home_dir = os.path.expanduser("~")
config_dir = os.path.join(home_dir, ".config")
config_file = os.path.join(config_dir, "ghostwraiter.json")

# Ensure the config directory exists
os.makedirs(config_dir, exist_ok=True)

# Default settings
default_settings = {
    "model_name": "",
    "max_tokens": 4096,
    "temperature": 0.5
}

# Load settings from file or use default settings
if os.path.exists(config_file):
    with open(config_file, "r") as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(config_file, "w") as f:
        json.dump(settings, f, indent=4)

def chat_with_model(prompt, context, model_name, max_tokens, temperature):
    # Use the ollama library to generate a response from the model
    response = ollama.generate(
        model=model_name,
        context=context,
        prompt=prompt,
        options={ "temperature": temperature, "max_tokens": max_tokens }
    )
    return response

def init():
    parser = argparse.ArgumentParser(description="Chat with a local AI model.")
    parser.add_argument("--model_name", type=str, help="Name of the model.")
    parser.add_argument("--max_tokens", type=int, help="Maximum number of tokens in the response.")
    parser.add_argument("--temperature", type=float, help="Sampling temperature.")

    args = parser.parse_args()

    # Update settings if provided
    if args.model_name:
        settings["model_name"] = args.model_name
    if args.max_tokens:
        settings["max_tokens"] = args.max_tokens
    if args.temperature:
        settings["temperature"] = args.temperature

    # Check if model_name is empty or not present
    if not settings.get("model_name"):
        running_models = ollama.list()
        if running_models:
            print("Available models:")
            for i, model in enumerate(running_models['models'], 1):
                print(f"{i}. {model['name']}")
            model_index = int(input("Please select the model number: ")) - 1
            settings["model_name"] = running_models['models'][model_index]['name']
        else:
            print("No running models found.")
            settings["model_name"] = input("Please enter the model name: ")

if __name__ == "__main__":
    init()
    context=""
    try:
        while True:
            prompt = input("You: ")
            response = chat_with_model(prompt, context, settings["model_name"], settings["max_tokens"], settings["temperature"])
            if response["context"]:
                context = response["context"]
            print(f"{settings['model_name']}: {response['response']}")
    except KeyboardInterrupt:
        print("\nExiting chat.")