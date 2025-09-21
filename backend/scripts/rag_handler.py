# proj/backend/scripts/rag_handler.py

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# --- SETUP ---

# 1. Define paths for persistent storage
scripts_dir = os.path.dirname(__file__)
db_path = os.path.join(scripts_dir, '..', 'data', 'chroma_db')
KNOWLEDGE_BASE_PATH = os.path.join(scripts_dir, '..', 'data', 'knowledge_base_manual.json') # Ensure this filename is correct!

# 2. Initialize clients and models
print("Initializing RAG Handler...")
model = SentenceTransformer('all-MiniLM-L6-v2')
# --- IMPROVEMENT #3: Use a PersistentClient ---
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection("singapore_housing_docs")

# --- DATA LOADING AND ONE-TIME INDEXING ---

def load_knowledge_base():
    """Loads the knowledge base from the JSON file."""
    try:
        with open(KNOWLEDGE_BASE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        return []

# --- IMPROVEMENT #2: Check if indexing is already done ---
if collection.count() == 0:
    print("Database is empty. Indexing knowledge base...")
    knowledge_data = load_knowledge_base()
    if knowledge_data:
        # --- IMPROVEMENT #1: Generate truly unique IDs ---
        collection.add(
            documents=[doc['content'] for doc in knowledge_data],
            ids=[f"{doc['source']}-{i}" for i, doc in enumerate(knowledge_data)]
        )
        print(f"Indexing complete. {collection.count()} documents added.")
else:
    print(f"Database already contains {collection.count()} documents. Skipping indexing.")


# --- CORE RAG LOGIC ---

def retrieve_context(user_msg, n_results=2):
    """Finds the most relevant document chunks from the vector database."""
    results = collection.query(
        query_texts=[user_msg],
        n_results=n_results
    )
    return "\n---\n".join(results['documents'][0]) if results and results['documents'] else None

def create_system_prompt(user_msg):
    """Retrieves context and constructs the final system prompt."""
    retrieved_context = retrieve_context(user_msg)

    # Note: I changed "HDB website" to be more general, since your data is now manual.
    system_prompt = (
        "You are an expert AI assistant for Singapore housing and rental policies. "
        "Answer the user's question in a conversational and helpful manner. "
    )

    if retrieved_context:
        # Changed "URL" to "source" which is more accurate for your manual data.
        system_prompt += (
            "Use the following provided CONTEXT to answer the user's QUESTION. "
            "Your answer should be primarily based on this context. You can mention the source of the information if it seems relevant.\n\n"
            "---CONTEXT---\n"
            f"{retrieved_context}"
        )
    else:
        system_prompt += "If you do not know the answer, say that you cannot find specific information in the knowledge base."
    
    return system_prompt