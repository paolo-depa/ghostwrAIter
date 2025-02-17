import argparse
import hashlib
import json
import os
import time
import sys

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings.fastembed  import FastEmbedEmbeddings

def parse_and_validate_args():
    parser = argparse.ArgumentParser(description="Vectorize text files in a directory using an embedding model.")
    parser.add_argument("--directory", type=str, default=".", help="Path to the directory containing text files.")
    parser.add_argument("--vector_dir", type=str, help="Path to the directory where the chromadb will be saved.")
    parser.add_argument("--ollama_url", type=str, help="URL for the Ollama service.")
    parser.add_argument("--ollama_embedding", type=str, help="Embedding model for the Ollama service.")
    parser.add_argument("--ollama_num_gpus", type=int, default=0, help="Number of GPUs to use for the Ollama service.")
    # not working with the current version of langchain-community
    # parser.add_argument("-r", "--recursive", action="store_true", help="Scan the directory recursively.")
    parser.add_argument("--exclude", action="append", help="Paths to exclude, enquoted in single quotes. Can be used multiple times.")
    args = parser.parse_args()

    # Verify that the directory is readable
    if not os.access(args.directory, os.R_OK):
        print(f"Directory {args.directory} is not readable.", file=sys.stderr)
        return None

    # Set default vector_dir if not provided
    if not args.vector_dir:
        args.vector_dir = os.path.join(args.directory, ".chroma.db")

    # 
    config_path = os.path.expanduser("~/.config/ghostwraiter/settings.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                if not args.ollama_url:
                    args.ollama_url = config.get("ollama.url")
                if not args.ollama_embedding:
                    args.ollama_embedding = config.get("ollama.embedding")
                if not args.ollama_num_gpus:
                    args.ollama_num_gpus = config.get("ollama.num_gpus")

        except (IOError, json.JSONDecodeError):
            print(f"Error reading configuration file {config_path}.", file=sys.stderr)

    # Add vector store base path to exclude paths
    if args.exclude is None:
        args.exclude = []
    args.exclude.append(args.vector_dir)

    return args

def calculate_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def update_exclude_and_content(args):
    content_file_path = os.path.join(args.vector_dir, ".content")
    content_data = {}

    # Load existing content data if available
    if os.path.exists(content_file_path):
        try:
            with open(content_file_path, 'r') as content_file:
                content_data = json.load(content_file)
        except (IOError, json.JSONDecodeError):
            print(f"Error reading content file {content_file_path}.", file=sys.stderr)
            return

    # Scan directory and calculate hashes
    for root, _, files in os.walk(args.directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path in args.exclude:
                continue
            file_hash = calculate_file_hash(file_path)
            if content_data.get(file_path) == file_hash:
                args.exclude.append(file_path)
                print(f"-- {file_path} already in the vector store.")
            else:
                content_data[file_path] = file_hash

    # Save updated content data
    try:
        os.makedirs(args.vector_dir, exist_ok=True)
        with open(content_file_path, 'w') as content_file:
            json.dump(content_data, content_file)
    except IOError:
        print(f"Error writing to content file {content_file_path}.", file=sys.stderr)

def main():
    args = parse_and_validate_args()
    if not args:
        return

    full_path = os.path.abspath(args.directory)
    collection_name = os.path.basename(full_path)

    # Running locally on GUI needs root privileges and fastembed-gui installed
    # embedding_function = FastEmbedEmbeddings(providers=["CUDAExecutionProvider"])
    embedding_function = FastEmbedEmbeddings(batch_size=512, parallel=0)
    if args.ollama_url and args.ollama_embedding:
        print(f"Embedding calculated at {args.ollama_url} with model {args.ollama_embedding}")
        embedding_function = OllamaEmbeddings(base_url=args.ollama_url, model=args.ollama_embedding, num_gpu=args.ollama_num_gpus)
    else:
        print(f"Embedding calculated locally using FastEmbeddings")
    
    update_exclude_and_content(args)

    try:
        loader = DirectoryLoader(
            path=args.directory,
            exclude=args.exclude,
            silent_errors=True,
            # recursive=args.recursive,
            use_multithreading=True,
            loader_cls=TextLoader
        )
        scan_start = time.time()
        print(f"Starting {full_path} scan at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(scan_start))}")
        splitted = loader.load_and_split()
        scan_end = time.time()
        print(f"Loaded {int(len(splitted))} chunks from {full_path} in {int(scan_end - scan_start)} seconds.")

    except Exception as e:
        print(f"Error adding documents to vector store: {e}")
        return

    try:
        vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=args.vector_dir,
            embedding_function=embedding_function
        )

        batch_size = 500
        total_docs = len(splitted)
        vector_start=time.time()
        print(f"Starting vector creation at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(vector_start))}")
        for i in range(0, total_docs, batch_size):
            batch = splitted[i:i + batch_size]
            ids = vector_store.add_documents(batch)
            vector_current = time.time()
            print(f"Added {(i + len(ids)) } / {total_docs} chunks to vector store in {int(vector_current - vector_start)} seconds.")

    except Exception as e:
        print(f"Error adding documents to vector store: {e}", file=sys.stderr)
        return

if __name__ == "__main__":
    main()
