## Project Giva: AI-Powered Document Q&A

### 1. Project Overview

Project Giva is a **Python-based RAG (Retrieval-Augmented Generation) system** that allows users to ask questions about their local documents. It leverages AI to provide insightful answers based on the content of provided files.

The core functionalities include:

*   **Document Ingestion:** Loads text files, splits them into chunks, creates embeddings, and stores them in a vector database for efficient searching.
*   **Query Enhancement:** Automatically expands short user queries to improve the relevance of search results.
*   **Conversational Memory:** Remembers the last few questions and answers to provide context-aware responses in an ongoing conversation.
*   **Advanced RAG Pipeline:** Retrieves relevant document chunks, assesses a confidence score, and generates a detailed, well-structured answer.
*   **Source Citing:** Lists the source documents (and pages) that were used to generate the answer, along with a relevance score for each.
*   **Interactive Console:** Provides a user-friendly command-line interface to interact with the system.
*   **API Endpoints:** Exposes health checks and a webhook for GitHub integration.

### 2. Setup and Initialization

1.  **Environment Variables:** Loads environment variables, specifically `GEMINI_API_KEY`.
2.  **Model Initialization:** Initializes the `ChatGoogleGenerativeAI` model (`gemini-1.5-flash`).
3.  **Component Initialization:** Creates instances of `EmbeddingPipeline`, `VectorStore`, and `RAGRetriever`.

### 3. Data Ingestion

*   The system checks if the vector store is already populated.
*   If not, it attempts to load all `.md` documents from the `data/text_files` directory.
*   If no documentation files are found, a warning is issued, and an empty index is created. The agent will still run but won't retrieve any information until documents are added and the agent is restarted.
*   The `EmbeddingPipeline` processes and embeds the documents, which are then added to the `VectorStore`.

### 4. Interactive Console Loop

*   An infinite `while` loop prompts the user for questions.
*   Special commands are supported:
    *   `exit` / `quit`: Terminates the application.
    *   `reset`: Clears the conversation history.
*   User queries are passed to `enhance_query_with_ai`.
*   The potentially enhanced query, along with the conversation history, is then processed by `rag_advanced`.

### 5. API Endpoints

*   **/api/health:** A GET endpoint that returns the current status of the Doc-Ops Agent.
*   **/api/stream/logs:** A WebSocket endpoint for streaming logs to the React frontend.
*   **/api/github/webhook:** An endpoint to receive and process GitHub webhooks for `pull_request` (merged) and `push` events.
    *   **Authentication:** Requires a valid `X-Hub-Signature-256` header for security.
    *   **Error Handling:** Provides specific error messages for missing or invalid signatures, and server configuration issues (e.g., missing `GITHUB_SECRET_TOKEN`).

### 6. Installation

*(Installation instructions would typically follow here in a full README)*

---

### Relevant Code Changes

```diff
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 3adee82..d729004 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -112,7 +112,7 @@ async def create_github_pr_async(*args, **kwargs):
 
 # --- Updated Core Agent Logic ---
 
-async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: int, user_name: str):
+async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
     """This is the main 'brain' of the agent. It runs the full analysis-retrieval-rewrite pipeline."""
     
     if not retriever:
diff --git a/backend/main.py b/backend/main.py
index 0ef8bc0..79e94c8 100644
--- a/backend/main.py
+++ b/backend/main.py
@@ -48,6 +48,11 @@ async def push_log(event: str, data: str):
     allow_headers=["*"],
 )
 
+
+# --- Health Check Endpoint ---
+@app.get("/api/health")
+async def health_check():
+    return {"status": "ok", "message": "Doc-Ops Agent is healthy"}
+
 # --- 1. The "Live Feed" Endpoint (for React) ---
 @app.get("/api/stream/logs")
 async def stream_logs(request: Request):
@@ -70,11 +75,11 @@ async def handle_github_webhook(
     raw_body = await request.body()
     
     if not GITHUB_SECRET_TOKEN:
-        print("ERROR: GITHUB_SECRET_TOKEN is not set!")
-        raise HTTPException(status_code=500, detail="Server configuration error")
+        print("ERROR: GITHUB_SECRET_TOKEN is not configured on the server.")
+        raise HTTPException(status_code=500, detail="Internal server error: Webhook secret not set.")
         
     if not x_hub_signature_256:
-        raise HTTPException(status_code=403, detail="Signature missing")
+        raise HTTPException(status_code=403, detail="X-Hub-Signature-256 header is missing.")
 
     hash_object = hmac.new(
         GITHUB_SECRET_TOKEN.encode('utf-8'),
@@ -84,8 +89,8 @@ async def handle_github_webhook(
     expected_signature = "sha256=" + hash_object.hexdigest()
 
     if not hmac.compare_digest(expected_signature, x_hub_signature_256):
-        print("ERROR: Invalid webhook signature")
-        raise HTTPException(status_code=403, detail="Invalid signature")
+        print("ERROR: Webhook signature mismatch.")
+        raise HTTPException(status_code=403, detail="Invalid webhook signature.")
 
     payload = await request.json()
 
@@ -192,5 +197,6 @@ if __name__ == "__main__":
     import uvicorn
     print("--- Starting Doc-Ops Agent Backend ---")
+    print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
     print("--- AI Models are warming up... ---")
     uvicorn.run(app, host="0.0.0.0", port=8000)
 \ No newline at end of file
diff --git a/backend/vector_store.py b/backend/vector_store.py
index d77d58f..cf4947e 100644
--- a/backend/vector_store.py
+++ b/backend/vector_store.py
@@ -37,23 +37,11 @@ def create_vector_store():
     
     try:
         documents = loader.load()
-        if not documents:
-            print(f"Error: No .md documents found in '{DATA_PATH}'.")
-            print("Please add your documentation files to the 'backend/data' folder.")
-            return None
     except Exception as e:
         print(f"Error loading documents: {e}")
         return None
 
-    # 2. Split the documents into smaller, searchable chunks
-    text_splitter = RecursiveCharacterTextSplitter(
-        chunk_size=1000,
-        chunk_overlap=100
-    )
-    docs = text_splitter.split_documents(documents)
-    print(f"Loaded and split {len(documents)} documents into {len(docs)} chunks.")
-
-# 2. Create embeddings (using local model)
+# 2. Create embeddings (using local model)
     print("Loading local embedding model... (This may download ~500MB on first run)")
     try:
         embeddings = HuggingFaceEmbeddings(
@@ -65,6 +53,23 @@ def create_vector_store():
         print(f"Error initializing local embedding model: {e}")
         return None
 
+# If no documents are found, create an empty index and save it.
+    if not documents:
+        print(f"Warning: No .md documents found in '{DATA_PATH}'. Creating an empty index.")
+        print("The agent will run, but won't find docs until you add them and restart.")
+        empty_faiss = FAISS.from_texts(["placeholder"], embeddings)
+        empty_faiss.delete([empty_faiss.index_to_docstore_id[0]])
+        empty_faiss.save_local(INDEX_PATH)
+        return empty_faiss
+
+# 2. Split the documents into smaller, searchable chunks
+    text_splitter = RecursiveCharacterTextSplitter(
+        chunk_size=1000,
+        chunk_overlap=100
+    )
+    docs = text_splitter.split_documents(documents)
+    print(f"Loaded and split {len(documents)} documents into {len(docs)} chunks.")
+
     # 4. Create FAISS index from documents and embeddings
     print("Creating FAISS index... This may take a moment.")
     try:
```