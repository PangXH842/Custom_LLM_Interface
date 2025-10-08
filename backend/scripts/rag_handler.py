# proj/backend/scripts/rag_handler.py

import json
import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

# --- SETUP ---
scripts_dir = os.path.dirname(__file__)
data_dir = os.path.join(scripts_dir, '..', 'data')
KNOWLEDGE_BASE_DIR = os.path.join(data_dir, 'jsons') # <-- THIS PATH IS UPDATED
db_path = os.path.join(data_dir, 'chroma_db')

print("Initializing RAG Handler...")
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=db_path)
main_collection = client.get_or_create_collection("singapore_housing_main")

def load_main_knowledge_base():
    """
    Loads all .json files from the knowledge base directory, combines them,
    and indexes them into the database if it's empty.
    """
    if main_collection.count() > 0:
        print(f"Main knowledge base already contains {main_collection.count()} documents.")
        return
    
    print("Main DB is empty. Searching for knowledge base files...")
    
    # Use glob to find all files ending with .json in the specified directory
    # IMPORTANT: We will exclude files from the 'uploads' and 'raw_html_pages' subdirectories.
    json_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, '*.json'))
    
    if not json_files:
        print(f"CRITICAL ERROR: No .json knowledge base files found in '{KNOWLEDGE_BASE_DIR}'")
        return

    all_knowledge_data = []
    print(f"Found {len(json_files)} files to process:")
    for file_path in json_files:
        print(f"  - Loading {os.path.basename(file_path)}")
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                # Ensure the data is a list before extending
                if isinstance(data, list):
                    all_knowledge_data.extend(data)
                else:
                    print(f"    - Warning: File '{os.path.basename(file_path)}' does not contain a JSON list. Skipping.")
        except json.JSONDecodeError:
            print(f"    - Warning: Could not decode JSON from '{os.path.basename(file_path)}'. Skipping.")
        except Exception as e:
            print(f"    - An unexpected error occurred with file '{os.path.basename(file_path)}': {e}")
            
    if all_knowledge_data:
        print(f"\nTotal documents loaded: {len(all_knowledge_data)}. Indexing into vector store...")
        
        # We need a globally unique ID, so we use enumerate on the combined list
        main_collection.add(
            documents=[doc['content'] for doc in all_knowledge_data],
            ids=[f"{doc.get('source', 'unknown_source')}-{i}" for i, doc in enumerate(all_knowledge_data)]
        )
        print(f"Indexing complete. {main_collection.count()} documents added to the main collection.")
    else:
        print("Warning: No valid data was loaded from any JSON file.")

load_main_knowledge_base()

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
def retrieve_context(user_msg, session_id):
    SIMILARITY_THRESHOLD = 1.0 
    QUERY_N_RESULTS = 5 
    filtered_context = []
    
    # 1. Search the main knowledge base
    main_results = main_collection.query(
        query_texts=[user_msg],
        n_results=QUERY_N_RESULTS,
        include=['documents', 'distances'] # IMPORTANT: We ask for the distances!
    )
    
    # Filter the results based on the distance score
    if main_results and main_results['distances']:
        for i, dist in enumerate(main_results['distances'][0]):
            if dist < SIMILARITY_THRESHOLD:
                filtered_context.append(main_results['documents'][0][i])
                print(f"  -> Found relevant doc (dist: {dist:.4f})") # Good for debugging

    # 2. Search the session-specific collection
    collection_name = f"session_{session_id}"
    try:
        if any(c.name == collection_name for c in client.list_collections()):
            session_collection = client.get_collection(name=collection_name)
            session_results = session_collection.query(
                query_texts=[user_msg],
                n_results=QUERY_N_RESULTS,
                include=['documents', 'distances']
            )
            # Filter these results as well
            if session_results and session_results['distances']:
                for i, dist in enumerate(session_results['distances'][0]):
                    if dist < SIMILARITY_THRESHOLD:
                        filtered_context.append(session_results['documents'][0][i])
                        print(f"  -> Found relevant doc from UPLOADED FILE (dist: {dist:.4f})")
    except Exception as e:
        print(f"Could not query session collection '{collection_name}': {e}")
        
    return "\n---\n".join(filtered_context) if filtered_context else None

def create_system_prompt(user_msg, session_id):
    # Retrieves context and constructs the final system prompt.
    # If no context is found, it creates a "helpful guide" prompt instead.
    retrieved_context = retrieve_context(user_msg, session_id)

    # This is the base personality for the bot in all scenarios.
    base_prompt = (
        "You are an expert AI assistant for Singapore housing and rental policies. "
        "Your primary goal is to help tenants understand their rights and obligations to prevent them from "
        "being taken advantage of due to information gaps. Your tone should be helpful, clear, and cautious. "
    )

    if retrieved_context:
        # --- SCENARIO 1: We found relevant context ---
        # Instruct the LLM to use the facts we found and add a cautious reminder.
        final_prompt = (
            base_prompt +
            "Answer the user's question conversationally using ONLY the following provided CONTEXT. "
            "Base your answer strictly on this context. Do not use outside knowledge. "
            "After answering, ALWAYS conclude with a friendly reminder for the user to double-check the specifics "
            "with their landlord or in their tenancy agreement, as every contract can be different.\n\n"
            "---CONTEXT---\n"
            f"{retrieved_context}"
        )
    else:
        # --- SCENARIO 2: No relevant context was found (The Professional Hybrid) ---
        # Instruct the LLM to answer from general knowledge BUT with a strong disclaimer.
        final_prompt = (
            base_prompt +
            "IMPORTANT: The user's question did not match any documents in your verified knowledge base. "
            "Your first task is to clearly state this to the user. "
            "Then, you may attempt to answer the question based on your general knowledge of common rental practices. "
            "You MUST include a clear and strong disclaimer that this information is from your general training, not from verified documents, "
            "and that it is crucial for them to verify this with their landlord and their specific tenancy agreement to avoid issues. "
            "Frame your response like this: 'While I couldn't find a specific match in my knowledge base for your question, here is some information based on my general training... [Your Answer] ... **Disclaimer:** This is general advice and not from a verified document. It is very important that you double-check these details with your landlord and your official tenancy agreement.'"
        )
    
    return final_prompt