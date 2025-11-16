import os
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings # <-- Changed import
from dotenv import load_dotenv

# --- Load API Key (still needed for LLM, but not for embeddings) ---
load_dotenv()

# --- Configuration ---
DATA_PATH = "data/"
INDEX_PATH = "faiss_index"

# --- Helper Functions ---

def create_vector_store():
    """
    Loads docs from the DATA_PATH, splits them, creates embeddings,
    and saves a new FAISS index to INDEX_PATH.
    """
    print(f"Creating new vector store from data in '{DATA_PATH}'...")

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
        db = FAISS.from_documents(docs, embeddings)
        
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
    return db.as_retriever(search_kwargs={"k": 3}) # Returns top 3 results


# --- Self-Test ---
if __name__ == "__main__":
    """
    This allows you to run this file directly to test it.
    
    1. Add a file named 'test.md' to the 'backend/data/' folder.
       Put some text in it like "The quick brown fox jumps over the lazy dog."
    2. Make sure you have run 'pip install -r requirements.txt'
    3. Run this command from the 'backend' directory:
       python vector_store.py
    
    It should create the index. Run it a second time to see it load the index.
    """
    
    print("--- Running Vector Store Self-Test ---")
    
    # Ensure data directory exists
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"Created '{DATA_PATH}' directory.")
        print("Please add your .md documentation files to this folder.")
        
    retriever = get_retriever()
    
    if retriever:
        print("\n--- Testing Retriever ---")
        try:
            test_query = "What does the fox do?"
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