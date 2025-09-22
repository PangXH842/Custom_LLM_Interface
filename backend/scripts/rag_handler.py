# proj/backend/scripts/rag_handler.py

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# --- SETUP ---
scripts_dir = os.path.dirname(__file__)
db_path = os.path.join(scripts_dir, '..', 'data', 'chroma_db')
KNOWLEDGE_BASE_PATH = os.path.join(scripts_dir, '..', 'data', 'knowledge_base_manual.json')

print("Initializing RAG Handler...")
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=db_path)

# --- MAIN (PERMANENT) KNOWLEDGE BASE ---
main_collection = client.get_or_create_collection("singapore_housing_main")

def load_main_knowledge_base():
    """Loads and indexes the main knowledge base if the collection is empty."""
    if main_collection.count() > 0:
        print(f"Main knowledge base already contains {main_collection.count()} documents.")
        return
    
    print("Main DB is empty. Indexing manual knowledge base...")
    try:
        with open(KNOWLEDGE_BASE_PATH, encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        if knowledge_data:
            main_collection.add(
                documents=[doc['content'] for doc in knowledge_data],
                ids=[f"{doc['source']}-{i}" for i, doc in enumerate(knowledge_data)]
            )
            print(f"Indexing complete. {main_collection.count()} documents added to main collection.")
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Main knowledge base file not found at {KNOWLEDGE_BASE_PATH}")

# Load the main KB on startup
load_main_knowledge_base()

# --- NEW: UPLOADED FILE HANDLING ---
def simple_chunker(text, chunk_size=300, chunk_overlap=50):
    """Splits text into overlapping chunks based on word count."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - chunk_overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def index_uploaded_file(file_path, session_id):
    """Reads, chunks, and indexes a user-uploaded text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Simple chunking strategy
        chunks = simple_chunker(text)
        
        # Create a new, session-specific collection
        collection_name = f"session_{session_id}"
        session_collection = client.get_or_create_collection(name=collection_name)
        
        # Clear old data if user re-uploads
        if session_collection.count() > 0:
            # client.delete_collection(name=collection_name)
            # session_collection = client.get_or_create_collection(name=collection_name)
            print(f"Collection '{collection_name}' already exists. Re-indexing.")


        if chunks:
            session_collection.add(
                documents=chunks,
                ids=[f"chunk_{i}" for i in range(len(chunks))]
            )
            print(f"Indexed {len(chunks)} chunks into collection '{collection_name}'.")

    except Exception as e:
        print(f"Error indexing file {file_path}: {e}")

# --- COMBINED RAG LOGIC ---
def retrieve_context(user_msg, session_id, n_results=2):
    """Searches both the main and session-specific collections for context."""
    all_context = []
    
    # 1. Search the main knowledge base
    main_results = main_collection.query(query_texts=[user_msg], n_results=n_results)
    if main_results and main_results['documents']:
        all_context.extend(main_results['documents'][0])

    # 2. Search the session-specific collection if it exists
    collection_name = f"session_{session_id}"
    try:
        # Check if collection exists without creating it if it doesn't
        if any(c.name == collection_name for c in client.list_collections()):
            session_collection = client.get_collection(name=collection_name)
            session_results = session_collection.query(query_texts=[user_msg], n_results=n_results)
            if session_results and session_results['documents']:
                all_context.extend(session_results['documents'][0])
    except Exception as e:
        print(f"Could not query session collection '{collection_name}': {e}")
        
    return "\n---\n".join(all_context) if all_context else None

def create_system_prompt(user_msg, session_id):
    """Retrieves combined context and constructs the final system prompt."""
    retrieved_context = retrieve_context(user_msg, session_id)

    system_prompt = (
        "You are an expert AI assistant for Singapore housing and rental policies. "
        "Answer the user's question in a conversational and helpful manner. "
    )

    if retrieved_context:
        system_prompt += (
            "Use the following provided CONTEXT to answer the user's QUESTION. "
            "Some of the context may come from a user-uploaded document. "
            "Base your answer primarily on this context.\n\n"
            "---CONTEXT---\n"
            f"{retrieved_context}"
        )
    else:
        system_prompt += "If you do not know the answer, say that you cannot find specific information in the knowledge base."
    
    return system_prompt