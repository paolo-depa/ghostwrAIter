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
    try:
        with open(config_file, "r") as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print("Error decoding JSON from settings file. Using default settings.")
        settings = default_settings
else:
    settings = default_settings
    with open(config_file, "w") as f:
        json.dump(settings, f, indent=4)

def chat_with_model(prompt, context, model_name, max_tokens, temperature):
    """
    Generate a response from the model using the ollama library.
    
    Args:
        prompt (str): The input prompt for the model.
        context (str): The context to maintain conversation state.
        model_name (str): The name of the model to use.
        max_tokens (int): The maximum number of tokens in the response.
        temperature (float): The sampling temperature for response generation.
    
    Returns:
        dict: The response from the model.
    """
    try:
        response = ollama.generate(
            model=model_name,
            context=context,
            prompt=prompt,
            options={"temperature": temperature, "max_tokens": max_tokens}
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
            try:
                model_index = int(input("Please select the model number: ")) - 1
                settings["model_name"] = running_models['models'][model_index]['name']
            except (ValueError, IndexError):
                print("Invalid selection. Please enter a valid model number.")
                settings["model_name"] = input("Please enter the model name: ")
        else:
            print("No running models found.")
            settings["model_name"] = input("Please enter the model name: ")

if __name__ == "__main__":
    init()
    context = ""
    try:
        while True:
            prompt = input("You: ")
            response = chat_with_model(prompt, context, settings["model_name"], settings["max_tokens"], settings["temperature"])
            if "context" in response and response["context"]:
                context = response["context"]
            if "response" in response:
                print(f"{settings['model_name']}: {response['response']}")
            else:
                print(f"{settings['model_name']}: No response received.")

    except KeyboardInterrupt:
        print("\nExiting chat.")