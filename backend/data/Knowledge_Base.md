The `CONFIDENCE_THRESHOLD` environment variable can now be used to configure the minimum confidence score required for documentation updates. The default value is set to `0.2`.

## Core Technologies

-   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
-   **LangChain:** A framework for developing applications powered by language models. It allows for the chaining of different components, such as LLMs, prompt templates, and retrievers.
-   **FAISS:** A library for efficient similarity search and clustering of dense vectors. Used here to create a searchable index of the documentation.
-   **HuggingFace Embeddings:** Utilized for generating vector embeddings of text data, enabling semantic understanding and retrieval.
-   **Docker:** Used for containerizing the application, ensuring consistent environments across development and deployment.
-   **GitHub Webhooks:** To trigger the agent when code changes occur in a repository.

## Agent Logic (`agent_logic.py`)

*   **`run_agent_analysis`:** This is the core of the agent.
    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
    *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
    *   **Pull Request Creation:** Finally, it uses the `create_github_pr_async` function to create a new branch, stage the changes, and open a pull request on GitHub with the generated documentation.

## Vector Store (`vector_store.py`)

*   **`create_vector_store`:** This function is responsible for building the FAISS index. It takes a list of file paths, reads their content, and generates embeddings using a specified model. These embeddings are then stored in a FAISS index file (`docs.index`) and a mapping of document content to their embeddings (`doc_map.json`).
*   **`load_vector_store`:** This function loads the existing FAISS index and the document map from disk, allowing the agent to perform similarity searches.

## Broadcaster (`broadcaster.py`)

*   A utility for sending real-time status updates (logs, errors, actions) from the backend to connected clients (e.g., a frontend dashboard) via WebSockets.

## Environment Variables

*   `GITHUB_SECRET_TOKEN`: Used to verify incoming GitHub webhooks.
*   `GITHUB_API_TOKEN`: Used by the agent to authenticate with the GitHub API for fetching diffs and creating pull requests.
*   `OPENAI_API_KEY`: Your OpenAI API key.
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
-         *   Use `10000` for the port as recommended by Render.
+         *   Use the port recommended by Render (e.g., `10000`).
  3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
  4.  **Deploy**: Trigger a manual deploy.
  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 194eafb..3b3f53d 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -199,5 +199,4 @@
             if confidence_score < confidence_threshold: # Gatekeeping based on confidence
                  await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                  return
-
 ```
```