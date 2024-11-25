import chromadb

client = chromadb.PersistentClient(vector_file)
collection = client.get_or_create_collection(name=collection_name)

results = collection.query(
    query_texts=[query_text]
)