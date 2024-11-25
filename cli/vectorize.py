import os
import argparse
import json
import time

import langchain_ollama
from langchain_ollama import OllamaEmbeddings
import langchain_text_splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter
import langchain_chroma
from langchain_chroma import Chroma
import langchain_community
from langchain_community.document_loaders import DirectoryLoader, TextLoader

import chromadb
from chromadb.utils import embedding_functions

def parse_and_validate_args():
    parser = argparse.ArgumentParser(description="Vectorize text files in a directory using an embedding model.")
    parser.add_argument("--directory", type=str, default=".", help="Path to the directory containing text files.")
    parser.add_argument("--vector_dir", type=str, help="Path to the file where the chromadb will be saved.")
    parser.add_argument("--ollama_url", type=str, help="URL for the Ollama service.")
    parser.add_argument("--ollama_embedding", type=str, help="Embedding model for the Ollama service.")
    args = parser.parse_args()

    if not args.directory:
        args.directory = "."

    # Verify that the directory is readable
    if not os.access(args.directory, os.R_OK):
        print(f"Directory {args.directory} is not readable.")
        return None

    # Set default vector_dir if not provided
    if not args.vector_dir:
        args.vector_dir = os.path.join(args.directory, ".chroma.db")

    # Check for ollama_url argument or read from config file
    if not args.ollama_url or not args.ollama_embedding:
        config_path = os.path.expanduser("~/.config/ghostwraiter/settings.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as config_file:
                    config = json.load(config_file)
                    if not args.ollama_url:
                        args.ollama_url = config.get("ollama.url")
                    if not args.ollama_embedding:
                        args.ollama_embedding = config.get("ollama.embedding")
            except (IOError, json.JSONDecodeError):
                print(f"Error reading configuration file {config_path}.")
                return None

    return args

def main():
    args = parse_and_validate_args()
    if not args:
        return

    full_path = os.path.abspath(args.directory)
    collection_name = os.path.basename(full_path)

    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    if (args.ollama_url and args.ollama_embedding):
        embedding_function = OllamaEmbeddings(base_url=args.ollama_url, model=args.ollama_embedding)
    
    try:
        loader = DirectoryLoader(path=args.directory, exclude=args.vector_dir, silent_errors=True, recursive=True,use_multithreading=True,loader_cls=TextLoader)
        splitted = loader.load_and_split()
        print(f"Loaded {len(splitted)} documents from {full_path}")
    except Exception as e:
        print(f"Error adding documents to vector store: {e}")
        return

    try:
         vector_store = Chroma(collection_name=collection_name, persist_directory=args.vector_dir,embedding_function=embedding_function)
         ids=vector_store.add_documents(splitted)
         print(f"Added {len(ids)} documents to vector store in {full_path}")
    except Exception as e:
        print(f"Error adding documents to vector store: {e}")
        return

if __name__ == "__main__":
    main()
