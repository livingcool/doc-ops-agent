2.  **Agent Logic (`agent_logic.py`):**
    *   **`run_agent_analysis`:** This is the core of the agent.
        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
        *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.

---
### Relevant Code Changes
```diff
diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
index 36e9b76..4ec729c 100644
--- a/backend/data/Knowledge_Base.md
+++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@ The system is designed around a central FastAPI application that listens for Git
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
-                 return
- 
-```
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
++++ b/backend/data/Knowledge_Base.md
@@ -40,7 +40,7 @@
     *   **`run_agent_analysis`:** This is the core of the agent.
         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
 
 ---
 
-### AI-Generated Update (2025-11-16 11:47:09)
+## Agent Logic (`agent_logic.py`)
 
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
 
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+---
 
---- Snippet 2 (Source: agent_logic.py) ---
-# --- Step 9: Log the final result ---
+# Step 9: Log the final result
         if "Successfully" in result_message:
             # On success, log the specific format you requested.
             log_entry = (
@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return
 
---- Snippet 3 (Source: agent_logic.py) ---
+---
+
 def _append_to_file_sync(file_path: str, content: str):
     """Synchronous file append operation."""
     with open(file_path, "a", encoding="utf-8") as f:
@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         await broadcaster("log-error", "Error: Agent AI components are not ready.")
         return
 
---- Snippet 4 (Source: agent_logic.py) ---
+---
+
 if "Error" in pr_url:
                 result_message = f"Failed to create PR. Reason: {pr_url}"
                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
@@ -139,44 +132,10 @@ if "Error" in pr_url:
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         
 ---
-### Relevant Code Changes
-```diff
-diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
-index 31b5e7c..629049c 100644
---- a/backend/USER_GUIDE.md
-+++ b/backend/USER_GUIDE.md
-@@ -86,6 +86,9 @@ The backend is a Python FastAPI application.
- 
-     # Your OpenAI API key
-     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-+
-+    # (Optional) The minimum confidence score required to update a document
-+    CONFIDENCE_THRESHOLD=0.2
-     ```
- 
- ### Step 3: Frontend Setup
-@@ -203,7 +206,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
-     *   **Build Command**: `pip install -r requirements.txt`
-         *   This is usually the default and is correct.
-     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
--        *   Use `10000` for the port as recommended by Render.
-+        *   Use the port recommended by Render (e.g., `10000`).
- 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
- 4.  **Deploy**: Trigger a manual deploy.
- 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
-diff --git a/backend/agent_logic.py b/backend/agent_logic.py
-index 194eafb..3b3f53d 100644
---- a/backend/agent_logic.py
-+++ b/backend/agent_logic.py
-@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
-             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
-         else:
-             # --- UPDATE MODE ---
--            if confidence_score < 0.2: # Gatekeeping based on confidence
-+            # Make the confidence threshold configurable for easier testing
-+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
-+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
-