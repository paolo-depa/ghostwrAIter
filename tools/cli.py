import os
import json
import argparse

from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain import hub

# Define the path for the settings file
home_dir = os.path.expanduser("~")
config_dir = os.path.join(home_dir, ".config/ghostwraiter")
config_file = os.path.join(config_dir, "settings.json")

# Ensure the config directory exists
os.makedirs(config_dir, exist_ok=True)

# Default settings
default_settings = {
    "ollama.model": "",
    "ollama.temperature": 0.5,
    "ollama.url": "localhost:11434",
    "vector.parent_dir": "./.chroma.db"
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

def parse_args():
    parser = argparse.ArgumentParser(description="Chat with a local AI model.")
    parser.add_argument("--model", type=str, help="Name of the model.")
    parser.add_argument("--temperature", type=float, help="Sampling temperature.")
    parser.add_argument("--url", type=str, help="URL of the Ollama server.")
    parser.add_argument("--vector_parent_dir", type=str, default=".", help="Parent directory where the .chroma.db folder can be found")
    parser.add_argument("--prompt_template", type=str, required=True, help="Path to the prompt template file.")

    args = parser.parse_args()

    # Update settings if provided
    if args.model:
        settings["ollama.model"] = args.model
    if args.temperature:
        settings["ollama.temperature"] = args.temperature
    if args.url:
        settings["ollama.url"] = args.url
    if args.vector_parent_dir:
        settings["vector.parent_dir"] = args.vector_parent_dir

    if not os.path.isdir(settings["vector.parent_dir"]):
        print(f"Error: The directory {settings['vector.parent_dir']} does not exist.", file=sys.stderr)
        exit(1)

    settings['vector.collection_name'] = os.path.basename(os.path.abspath(settings["vector.parent_dir"]))

    settings["vector.dir"] = os.path.join(settings["vector.parent_dir"], ".chroma.db")
    if not os.path.isdir(settings["vector.dir"]):
        print(f"Error: The directory {settings['vector.dir']} does not exist.", file=sys.stderr)
        exit(1)

    settings["vector.parent_dir"] = os.path.join(os.path.abspath(settings["vector.parent_dir"]), ".chroma.db")

    if not settings["ollama.model"]:
        print("Error: Model name is required.")
        exit(1)

    if args.prompt_template:
        if not os.path.isfile(args.prompt_template):
            print(f"Error: The file {args.prompt_template} does not exist.", file=sys.stderr)
            exit(1)
        try:
            with open(args.prompt_template, "r") as f:
                prompt_content = f.read()
            if "{context}" not in prompt_content or "{question}" not in prompt_content:
                print("Error: The prompt template must contain {context} and {question} placeholders.", file=sys.stderr)
                exit(1)
            settings["prompt_template"] = PromptTemplate.from_template(prompt_content)
        except Exception as e:
            print(f"Error reading prompt template file: {e}", file=sys.stderr)
            exit(1)
    else:
        print("Error: Prompt template file is required.", file=sys.stderr)
        exit(1)

    return settings

if __name__ == "__main__":
    settings = parse_args()

    llm = OllamaLLM(
        base_url=settings["ollama.url"],
        model=settings["ollama.model"],
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )

    try:
        vectorstore = Chroma(
            collection_name=settings['vector.collection_name'],
            create_collection_if_not_exists=False,
            persist_directory=settings["vector.parent_dir"]
        )
    except Exception as e:
        print(f"Error loading vector store: {e}", file=sys.stderr)
        exit(1)

    while True:
        qa_chain = (
            {
                "context": vectorstore.as_retriever(),
                "question": RunnablePassthrough(),
            }
            | settings["prompt_template"]
            | llm
            | StrOutputParser()
        )

        query = input("\nYou: ")
        try:
            result = qa_chain.invoke(query)
        except Exception as e:
            print(f"Error: {e}")
