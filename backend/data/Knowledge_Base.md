The `CONFIDENCE_THRESHOLD` environment variable can now be used to configure the minimum confidence score required for documentation updates. The default value is set to `0.2`.

## Agent Logic (`agent_logic.py`)

*   **`run_agent_analysis`:** This is the core of the agent.
    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.

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
-        *   Use `10000` for the port as recommended by Render.
+        *   Use the port recommended by Render (e.g., `10000`).
 3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
 4.  **Deploy**: Trigger a manual deploy.
 5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 194eafb..3b3f53d 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -197,7 +197,9 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
         else:
             # --- UPDATE MODE ---
-            if confidence_score < 0.2: # Gatekeeping based on confidence
+            # Make the confidence threshold configurable for easier testing
+            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
+            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
                 await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                 return

```