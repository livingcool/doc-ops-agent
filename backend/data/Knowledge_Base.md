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
-
-2.  **Agent Logic (`agent_logic.py`):**
-    *   **`run_agent_analysis`:** This is the core of the agent.
-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
-
---- Snippet 1 (Source: data\Knowledge_Base.md) ---
- 2.  **Agent Logic (`agent_logic.py`):**
-     *   **`run_agent_analysis`:** This is the core of the agent.
-         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
-@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
-         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
-         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
-         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+## Agent Logic (`agent_logic.py`)
+
+*   **`run_agent_analysis`:** This is the core of the agent.
+    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+
+---- Snippet 2 (Source: agent_logic.py) ---
+# --- Step 9: Log the final result ---
+         if "Successfully" in result_message:
+             # On success, log the specific format you requested.
+             log_entry = (
+@@ -108,7 +99,8 @@ await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
+                 return
+ 
+---- Snippet 3 (Source: agent_logic.py) ---
+---
+
+ def _append_to_file_sync(file_path: str, content: str):
+     """Synchronous file append operation."""
+     with open(file_path, "a", encoding="utf-8") as f:
+@@ -124,7 +116,8 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         await broadcaster("log-error", "Error: Agent AI components are not ready.")
+         return
+ 
+---- Snippet 4 (Source: agent_logic.py) ---
+---
+
+ if "Error" in pr_url:
+                 result_message = f"Failed to create PR. Reason: {pr_url}"
+                 await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+@@ -139,44 +132,10 @@ if "Error" in pr_url:
+             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+         
+ ---
+### Relevant Code Changes
+```diff
+diff --git a/backend/data/Knowledge_Base.md b/backend/data/Knowledge_Base.md
+index 36e9b76..4ec729c 100644
+--- a/backend/data/Knowledge_Base.md
+++++ b/backend/data/Knowledge_Base.md
+@@ -40,7 +40,7 @@
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+         *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
++        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+         *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
+@@ -68,27 +68,18 @@ In essence, the system acts as an automated documentation assistant. It watches
+ 
+ ---
+ 
+-### AI-Generated Update (2025-11-16 11:47:09)
+-
+-2.  **Agent Logic (`agent_logic.py`):**
+-    *   **`run_agent_analysis`:** This is the core of the agent.
+-        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+-        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+-        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+-        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+-        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
+-
+---- Snippet 1 (Source: data\Knowledge_Base.md) ---
+ 2.  **Agent Logic (`agent_logic.py`):**
+     *   **`run_agent_analysis`:** This is the core of the agent.
+         *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
+@@ -86,118 +5,3162 @@ In essence, the system acts as an automated documentation assistant. It watches
+         *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+         *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+         *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.