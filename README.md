# GhostwrAIter

## Project Overview

GhostwrAIter is a project designed to build and query a permanent vector database out of a local directory containing logs, outputs of Linux commands, and descriptions of occurring issues.
The databases is then passed as context when chatting with an LLM in a RAG fashion.

The main components of the project are:

1. **Vectorization**: Using `bin/vectorize.py`, the project calculates embeddings from the data in the local directory and stores them in a permanent vector database.
2. **Chat**: Using `bin/chat.py`, the LLM of choice can be interrogated using prompt templates from the `prompts` folder and providing the vectorized database as context.


## Setup

To set up the project, use the scripts in the `setup` folder: please consider them more as guidelines to be adapted on different environments (they have been krafted on a SLES 15SP5 and are tested only there so far...)

In a nutshell, the setup configures an ollama running instance and pulls models for calculating the embeddings to be stored in the vector database and (other) models for chat interaction, giving precedence to code-generation optimized ones.


## Folder Structure

- `setup/`: Contains tools and configuration files for setting up the Ollama instance.
- `prompts/`: Contains prompt templates for querying the Ollama instance.
- `bin/`: Contains the scripts referenced in the overview
- `tools/`: Contains tools to be used for filling the local directory with contents

