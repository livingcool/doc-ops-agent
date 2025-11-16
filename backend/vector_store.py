import os
import faiss
import asyncio
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings # <-- Changed import
from dotenv import load_dotenv
from llm_clients import get_seeder_chain # For initial knowledge seeding

# --- Load API Key (still needed for LLM, but not for embeddings) ---
load_dotenv()

# --- Configuration ---
DATA_PATH = "data/"
INDEX_PATH = "faiss_index"

# --- Helper Functions ---

def _seed_initial_knowledge():
    """
    If the main knowledge base is empty, this function populates it with an
    auto-generated summary of the project's source code.
    """
    knowledge_base_path = os.path.join(DATA_PATH, "Knowledge_Base.md")
    
    # Check if the guide is empty or just has placeholder content
    if os.path.exists(knowledge_base_path) and os.path.getsize(knowledge_base_path) > 100:
        return # Knowledge base already exists

    print("🌱 Knowledge base is empty. Seeding initial knowledge from source code...")
    
    try:
        # Read the content of the key source files
        source_files = ['main.py', 'agent_logic.py', 'vector_store.py']
        source_code = ""
        for file_name in source_files:
            with open(file_name, 'r', encoding='utf-8') as f:
                source_code += f"--- {file_name} ---\n{f.read()}\n\n"
        
        # Get the LLM chain to generate the summary
        seeder_chain = get_seeder_chain()
        
        # Generate the initial knowledge base content
        initial_knowledge = seeder_chain.invoke({"source_code": source_code})
        
        # Write the content to the USER_GUIDE.md
        with open(knowledge_base_path, 'w', encoding='utf-8') as f:
            f.write(initial_knowledge)
            
        print("✅ Successfully seeded knowledge base with project summary.")

    except Exception as e:
        print(f"🔥 Error seeding knowledge base: {e}")

def create_vector_store():
    """
    Loads docs from the DATA_PATH, splits them, creates embeddings,
    and saves a new FAISS index to INDEX_PATH.
    """
    print(f"Creating new vector store from data in '{DATA_PATH}'...")

    # --- NEW: Seed knowledge if the guide is empty ---
    _seed_initial_knowledge()

    # Define loader arguments to handle encoding errors
    loader_kwargs = {'encoding': 'utf-8', 'autodetect_encoding': True} # <-- Encoding fix

    # 1. Load all .md documents from the /data directory
    loader = DirectoryLoader(
        DATA_PATH, 
        glob="**/*.md", 
        loader_cls=TextLoader,
        loader_kwargs=loader_kwargs,  # <-- Added loader_kwargs
        show_progress=True,
        use_multithreading=True
    )
    
    try:
        documents = loader.load()
    except Exception as e:
        print(f"Error loading documents: {e}")
        return None

    # 2. Create embeddings (using local model)
    print("Loading local embedding model... (This may download ~500MB on first run)")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'} # Use CPU
        )
        print("Embedding model loaded.")
    except Exception as e:
        print(f"Error initializing local embedding model: {e}")
        return None

    # If no documents are found, create an empty index and save it.
    if not documents:
        print(f"Warning: No .md documents found in '{DATA_PATH}'. Creating an empty index.")
        print("The agent will run, but won't find docs until you add them and restart.")
        empty_faiss = FAISS.from_texts(["placeholder"], embeddings)
        empty_faiss.delete([empty_faiss.index_to_docstore_id[0]])
        empty_faiss.save_local(INDEX_PATH)
        return empty_faiss

    # 2. Split the documents into smaller, searchable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    docs = text_splitter.split_documents(documents)
    print(f"Loaded and split {len(documents)} documents into {len(docs)} chunks.")

    # 4. Create FAISS index from documents and embeddings
    print("Creating FAISS index... This may take a moment.")
    try:
        # --- THIS IS THE FIX ---
        # Use the COSINE distance strategy, which is what the retriever expects and works correctly with the embedding model.
        db = FAISS.from_documents(docs, embeddings, distance_strategy="COSINE")
        
        # 5. Save the index locally
        db.save_local(INDEX_PATH)
        print(f"Successfully created and saved index to '{INDEX_PATH}'.")
        return db
    except Exception as e:
        print(f"Error creating or saving FAISS index: {e}")
        return None


def load_vector_store():
    """
    Loads an existing FAISS index from INDEX_PATH.
    """
    
    # Check if the index files exist
    if not os.path.exists(f"{INDEX_PATH}/index.faiss") or not os.path.exists(f"{INDEX_PATH}/index.pkl"):
        print(f"No index found at '{INDEX_PATH}'.")
        return None

    print(f"Loading existing index from '{INDEX_PATH}'...")
    
    try:
        # Re-initialize the same local embeddings model
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Load the local index
        db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True) # Hackathon-safe
        print("Successfully loaded index.")
        return db
    except Exception as e:
        print(f"Error loading index. Did you create it first? {e}")
        return None

def add_docs_to_store(new_docs: list):
    """
    Incrementally adds new documents to the existing vector store.
    """
    print(f"Incrementally adding {len(new_docs)} new documents to the vector store...")
    db = load_vector_store()
    if db is None:
        print("Warning: No vector store found to add to. Triggering a full rebuild.")
        create_vector_store()
        return

    try:
        # Split the new documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        docs_to_add = text_splitter.split_documents(new_docs)
        
        # Add the new chunks to the existing FAISS index
        db.add_documents(docs_to_add)
        
        # Save the updated index back to disk
        db.save_local(INDEX_PATH)
        print("✅ Successfully added new documents and saved the updated index.")
        
        # Update the global retriever with the new db state
        global retriever
        retriever = db.as_retriever(search_type="mmr", search_kwargs={'k': 5, 'fetch_k': 20})
    except Exception as e:
        print(f"🔥 Error adding documents to vector store: {e}")

# --- Main Retriever Function ---

def get_retriever():
    """
    The main function called by the agent.
    Tries to load an existing index. If it fails,
    it creates a new one.
    Returns a LangChain retriever object.
    """
    db = load_vector_store()
    
    if db is None:
        print("No existing index found, creating a new one...")
        db = create_vector_store()
        if db is None:
            raise Exception("Failed to create vector store. Check errors above.")

    # Convert the vector store into a retriever
    # This is what our agent will use to find relevant docs
    # --- THIS IS THE FIX ---
    # Switch to 'mmr' (Maximal Marginal Relevance) search type. It's more robust,
    # works correctly with COSINE distance, and provides more diverse results.
    # We remove the score_threshold here to let the agent logic handle confidence checking.
    return db.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 20} # Always fetch the top 5 diverse results
    )


# --- Self-Test ---
if __name__ == "__main__":
    """
    This allows you to run this file directly to create, test, or rebuild the index.
    
    Usage:
    - To create/test the index:
      python vector_store.py
    
    - To force a rebuild of the index (deletes the old one):
      python vector_store.py --rebuild
    """
    import sys
    import shutil
    
    print("--- Running Vector Store Self-Test ---")

    # --- ADDED: Command-line flag to force a rebuild ---
    if len(sys.argv) > 1 and sys.argv[1] == '--rebuild':
        if os.path.exists(INDEX_PATH):
            print(f"Found '--rebuild' flag. Deleting old index at '{INDEX_PATH}'...")
            try:
                shutil.rmtree(INDEX_PATH)
                print("Old index deleted successfully.")
            except Exception as e:
                print(f"Error deleting index directory: {e}")
                sys.exit(1)
        else:
            print(f"Found '--rebuild' flag, but no index exists at '{INDEX_PATH}'. Proceeding to create a new one.")
    # --- END OF ADDITION ---
    
    # Ensure data directory exists
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"Created '{DATA_PATH}' directory.")
        print("Please add your .md documentation files to this folder.")

    # Add a dummy file if the data directory is empty to aid first-time users
    if not os.listdir(DATA_PATH):
        print(f"Warning: The '{DATA_PATH}' directory is empty.")
        print("Please add your project's documentation (.md files) here for the agent to work correctly.")
        
    retriever = get_retriever()
    
    if retriever:
        print("\n--- Testing Retriever ---")
        try:
            test_query = "What does this project do ?"
            results = retriever.invoke(test_query)
            print(f"Query: '{test_query}'")
            print(f"Results: ({len(results)} found)")
            for i, doc in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"Content: {doc.page_content[:150]}...")
            print("\nSelf-test complete. Retriever is working.")
        except Exception as e:
            print(f"Error testing retriever: {e}")