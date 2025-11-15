import os
import faiss
import shutil
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# --- Load API Key (still needed for LLM, but not for embeddings) ---
load_dotenv()

# --- Configuration ---
# NOW A BASE PATH FOR *ALL* USERS
BASE_INDEX_PATH = "faiss_indexes" 

# --- Embedding Model (Load once) ---
try:
    print("Loading shared embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("✅ Shared embedding model loaded.")
except Exception as e:
    print(f"🔥 FATAL: Could not load embedding model: {e}")
    embeddings = None

# --- NEW: Function to build an index for a *new user* ---
def create_user_vector_store(user_id: str, docs_path: str):
    """
    Scans a folder of docs, creates an index, and saves it
    to a user-specific path (e.g., 'faiss_indexes/user_1234')
    """
    if not embeddings:
        raise Exception("Embedding model is not loaded.")
        
    user_index_path = os.path.join(BASE_INDEX_PATH, user_id)
    
    # Clean up old index if it exists
    if os.path.exists(user_index_path):
        shutil.rmtree(user_index_path)
    
    print(f"Creating new vector store for user '{user_id}' from '{docs_path}'...")

    loader_kwargs = {'encoding': 'utf-8', 'autodetect_encoding': True}
    loader = DirectoryLoader(
        docs_path, 
        glob="**/*.md", # Only find markdown files
        loader_cls=TextLoader,
        loader_kwargs=loader_kwargs,
        show_progress=True,
        use_multithreading=True,
        silent_errors=True # Skip files it can't read
    )
    
    try:
        documents = loader.load()
    except Exception as e:
        print(f"Error loading documents for user: {e}")
        return False # Failed

    if not documents:
        print(f"No .md documents found for user '{user_id}' in '{docs_path}'.")
        return False # Failed

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(docs)} chunks for user '{user_id}'.")

    try:
        db = FAISS.from_documents(docs, embeddings)
        db.save_local(user_index_path)
        print(f"Successfully saved index for user '{user_id}' to '{user_index_path}'.")
        return True # Success
    except Exception as e:
        print(f"Error creating/saving FAISS index for user '{user_id}': {e}")
        return False # Failed

# --- UPDATED: Function to load an index for a *specific user* ---
def load_user_vector_store(user_id: str):
    """
    Loads an existing FAISS index for a specific user.
    """
    if not embeddings:
        raise Exception("Embedding model is not loaded.")

    user_index_path = os.path.join(BASE_INDEX_PATH, user_id)
    
    if not os.path.exists(f"{user_index_path}/index.faiss"):
        print(f"No index found for user '{user_id}' at '{user_index_path}'.")
        return None

    print(f"Loading existing index for user '{user_id}'...")
    
    try:
        db = FAISS.load_local(user_index_path, embeddings, allow_dangerous_deserialization=True)
        print(f"Successfully loaded index for user '{user_id}'.")
        return db
    except Exception as e:
        print(f"Error loading index for user '{user_id}': {e}")
        return None

# --- UPDATED: Main retriever function ---
# THIS IS THE FUNCTION THE ERROR IS ASKING FOR
def get_user_retriever(user_id: str):
    """
    Gets a retriever for a specific user.
    
    NOTE: In this new design, we *expect* the index to exist.
    The 'create_user_vector_store' function is now called
    during user onboarding, not on-the-fly.
    """
    db = load_user_vector_store(user_id)
    
    if db is None:
        print(f"Could not load vector store for user '{user_id}'.")
        return None

    return db.as_retriever(search_kwargs={"k": 3})

# --- Self-Test (No longer relevant, run main.py) ---
if __name__ == "__main__":
    print("This file is not meant to be run directly.")
    print("Run create_user_vector_store() to test.")