import os
import json
import argparse
import ollama
from ollama import Client

# Define the path for the settings file
home_dir = os.path.expanduser("~")
config_dir = os.path.join(home_dir, ".config")
config_file = os.path.join(config_dir, "ghostwraiter.json")

# Ensure the config directory exists
os.makedirs(config_dir, exist_ok=True)

# Default settings
default_settings = {
    "ollama.model": "",
    "ollama.temperature": 0.5,
    "ollama.url": "http://localhost:11434"
}

# Load settings from file or use default settings
if os.path.exists(config_file):
    try:
        with open(config_file, "r") as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print("Error decoding JSON from settings file. Using default settings.")
        settings = default_settings
else:
    settings = default_settings


def chat_with_model(prompt, context, model_name, temperature, url):
    """
    Generate a response from the model using the ollama library.
    
    Args:
        prompt (str): The input prompt for the model.
        context (str): The context to maintain conversation state.
        model_name (str): The name of the model to use.
        temperature (float): The sampling temperature for response generation.
        url (str): The URL of the Ollama server.
    
    Returns:
        dict: The response from the model.
    """
    try:
        client = Client(host=url)
        response = client.generate(
            model=model_name,
            context=context,
            prompt=prompt,
            options={"temperature": temperature}
        )
        return response
    except Exception as e:
        print(f"Error generating response: {e}")
        return {"response": "", "context": context}

def init():
    """
    Initialize the command-line interface, parse arguments, and update settings.
    """
    parser = argparse.ArgumentParser(description="Chat with a local AI model.")
    parser.add_argument("--model", type=str, help="Name of the model.")
    parser.add_argument("--temperature", type=float, help="Sampling temperature.")
    parser.add_argument("--url", type=str, help="URL of the Ollama server.")

    args = parser.parse_args()

    # Update settings if provided
    if args.model:
        settings["ollama.model"] = args.model
    if args.temperature:
        settings["ollama.temperature"] = args.temperature
    if args.url:
        settings["ollama.url"] = args.url

    # Check if model_name is empty or not present
    if not settings.get("ollama.model"):
        running_models = ollama.list()
        if running_models:
            print("Available models:")
            for i, model in enumerate(running_models['models'], 1):
                print(f"{i}. {model['name']}")
            try:
                model_index = int(input("Please select the model number: ")) - 1
                settings["ollama.model"] = running_models['models'][model_index]['name']
            except (ValueError, IndexError):
                print("Invalid selection. Please enter a valid model number.")
                settings["ollama.model"] = input("Please enter the model name: ")
        else:
            print("No running models found.")
            settings["ollama.model"] = input("Please enter the model name: ")

if __name__ == "__main__":
    init()
    context = ""
    try:
        while True:
            prompt = input("You: ")
            response = chat_with_model(prompt, context, settings["ollama.model"], settings["ollama.temperature"], settings["ollama.url"])
            if "context" in response and response["context"]:
                context = response["context"]
            if "response" in response:
                print(f"{settings['ollama.model']}: {response['response']}")
            else:
                print(f"{settings['ollama.model']}: No response received.")

    except KeyboardInterrupt:
        print("\nExiting chat.")
