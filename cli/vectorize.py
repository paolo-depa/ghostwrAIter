import os
import argparse
import json
import chromadb
import ollama
from ollama import Client
import hashlib
import time

def is_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file.read()
        return True
    except (UnicodeDecodeError, IOError):
        return False

def embed_text(text, ollama_url, ollama_embedding):
    client = Client(host=ollama_url)
    try:
        response = client.embed(model=ollama_embedding, input=text)
        return response
    except Exception as e:
        print(f"Error embedding text: {e}")
        return None

def parse_and_validate_args():
    parser = argparse.ArgumentParser(description="Vectorize text files in a directory using an embedding model.")
    parser.add_argument("--directory", type=str, default=".", help="Path to the directory containing text files.")
    parser.add_argument("--vector_file", type=str, help="Path to the file where the chromadb will be saved.")
    parser.add_argument("--ollama_url", type=str, help="URL for the Ollama service.")
    parser.add_argument("--ollama_embedding", type=str, help="Embedding model for the Ollama service.")
    args = parser.parse_args()

    if not args.directory:
        args.directory = "."

    # Verify that the directory is readable
    if not os.access(args.directory, os.R_OK):
        print(f"Directory {args.directory} is not readable.")
        return None

    # Set default vector_file if not provided
    if not args.vector_file:
        args.vector_file = os.path.join(args.directory, ".chroma.db")

    # Check for ollama_url argument or read from config file
    if not args.ollama_url or not args.ollama_embedding:
        config_path = os.path.expanduser("~/.config/ghostwraiter.json")
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

    client = chromadb.PersistentClient(args.vector_file)
    full_path = os.path.abspath(args.directory)
    collection_name = os.path.basename(full_path)
    collection = client.get_or_create_collection(name=collection_name)

    for root, _, files in os.walk(args.directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            vector_path=os.path.abspath(args.vector_file)
            # Skip the .chroma directory
            if os.path.abspath(file_path).startswith(vector_path):
                continue

            if is_text_file(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    file_size = os.path.getsize(file_path)
                    file_id = hashlib.md5(content.encode('utf-8')).hexdigest()
                    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())
                    print(f"{timestamp} - Processing file: {file_path}, hash: {file_id}, size: {file_size} bytes")

                    embedding = None
                    if args.ollama_url and args.ollama_embedding:
                         embedding = embed_text(content, args.ollama_url, args.ollama_embedding)

                    try:
                        if embedding and embedding['embeddings'] and embedding['model']:
                            collection.upsert(
                                documents=[content],
                                metadatas=[{"file_path": file_path, "embedding_model": embedding['model'] , "last_update": timestamp}],
                                ids=[file_id],
                                embeddings=[embedding['embeddings'][0]]
                            )
                        else:
                            # Let Chroma calculate the embeddings
                            collection.upsert(
                                documents=[content],
                                metadatas=[{"file_path": file_path, "last_update": timestamp}],
                                ids=[file_id]
                            )
                    except Exception as e:
                        print(f"    Error adding file to vector store: {e}")
                        continue

if __name__ == "__main__":
    main()
