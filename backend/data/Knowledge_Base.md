The `CONFIDENCE_THRESHOLD` environment variable can now be used to configure the minimum confidence score required for documentation updates. The default value is set to `0.2`.

## Core Technologies

The system is designed around a central FastAPI application that listens for Git events. Key components include:

1.  **FastAPI Backend (`main.py`):**
    *   Handles incoming GitHub webhooks (e.g., push events).
    *   Orchestrates the documentation generation and update process.
    *   Exposes API endpoints for potential future integrations.

2.  **Agent Logic (`agent_logic.py`):**
    *   **`run_agent_analysis`:** This is the core of the agent.
        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
        *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
        *   **Pull Request Creation:** Finally, it uses the `create_github_pr_async` function to create a new branch, stage the changes, and open a pull request on GitHub with the generated documentation.

3.  **Vector Store (`vector_store.py`):**
    *   **`create_vector_store`:** This function is responsible for building the FAISS index. It takes a list of file paths, reads their content, and generates embeddings using a specified model. These embeddings are then stored in a FAISS index file (`docs.index`) and a mapping of document content to their embeddings (`doc_map.json`).
    *   **`load_vector_store`:** This function loads the existing FAISS index and the document map from disk, allowing the agent to perform similarity searches.

4.  **Broadcaster (`broadcaster.py`):**
    *   A utility for sending real-time status updates (logs, errors, actions) from the backend to connected clients (e.g., a frontend dashboard) via WebSockets.

5.  **Environment Variables:**
    *   `GITHUB_SECRET_TOKEN`: Used to verify incoming GitHub webhooks.
    *   `GITHUB_API_TOKEN`: Used by the agent to authenticate with the GitHub API for fetching diffs and creating pull requests.
    *   `CONFIDENCE_THRESHOLD`: A float value (defaulting to 0.2) used to gate documentation updates. If the confidence score of retrieved documentation is below this threshold, the update is skipped.

In essence, the system acts as an automated documentation assistant. It watches for code changes, uses AI to understand them and interact with existing knowledge, updates that knowledge, and then proposes the documentation changes back to the project via a pull request.

---

### Relevant Code Changes

```diff
diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
index 31b5e7c..629049c 100644
--- a/backend/USER_GUIDE.md
+++ b/backend/USER_GUIDE.md
@@ -86,7 +86,7 @@ The backend is a Python FastAPI application.
     *   **Build Command**: `pip install -r requirements.txt`
         *   This is usually the default and is correct.
     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
-        ```
+```
 
     # Your OpenAI API key
     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
@@ -199,5 +199,4 @@ index 194eafb..3b3f53d 100644
             if confidence_score < confidence_threshold: # Gatekeeping based on confidence
                  await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                  return
-
```
```