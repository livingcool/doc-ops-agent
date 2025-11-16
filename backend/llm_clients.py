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
-
+    # (Optional) The minimum confidence score required to update a document
     # Your OpenAI API key
     OPENAI_API_KEY="sk-YourOpenAIKeyHere"
-
+    CONFIDENCE_THRESHOLD=0.2
     ```
 
 ### Step 3: Frontend Setup
@@ -199,5 +199,4 @@ index 194eafb..3b3f53d 100644
 +            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
                  await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                  return
- 
-```
+
```