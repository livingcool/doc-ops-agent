* The new question and the start of the AI's answer are appended to the `conversation_history`. The history is trimmed to the last 10 exchanges.
    * The results are displayed in a clean, formatted block.

| `rag_advanced(...)` | The primary, feature-rich RAG pipeline used by the application. | Retrieves documents based on the query, *top\_k* count, and a minimum similarity score (`min_score`). Constructs a list of **sources** (file name, page, similarity score). Calculates a **confidence** score (highest similarity score). Incorporates `conversation_history` into the LLM prompt. Uses a detailed, structured prompt to instruct the AI ("giva") on how to analyze and structure its answer. Returns a dictionary with `answer`, `sources`, `confidence`. |

💡 GIVA ANSWER:

Based on the provided documents, this project is a Retrieval-Augmented Generation (RAG) system designed to answer questions from a local document knowledge base.

Key features include:
* **AI-Powered Analysis:** It uses an AI assistant named "giva" to provide answers.
* **Source-Based Answers:** The system relies on context retrieved from documents to formulate its responses.
* **Conversational Context:** It can maintain a conversation history to provide more coherent answers over multiple questions.

📖 SOURCES (5 documents):

  1. 🔥 my_document_1.pdf (Page: 2) - Relevance: 0.8123
     Preview: ...The core of the RAG pipeline involves retrieving relevant text chunks from the indexed vector store and feeding them...
  2. 📄 another_doc.txt (Page: 1) - Relevance: 0.6543
     Preview: ...giva is an AI assistant specialized in analyzing and answering questions based on provided documents. Use the following...
  ...

#### Installation

---

### Relevant Code Changes

```diff
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 4484b9a..3adee82 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -207,23 +207,20 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             # Log the exception traceback for debugging
             logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
 
-        # --- Step 7: Create and write the detailed log entry ---
-        log_entry = f"""
-======================================================================
-AGENT RUN FOR PR #{pr_number}
-----------------------------------------------------------------------
-Repository:          {repo_name}
-Author:              @{user_name}
-Original PR Title:   '{pr_title}'
-AI Analysis:         {analysis_summary}
-----
-Generated Documentation:
-{new_documentation}
-----
-Result: {result_message}
-======================================================================
-"""
-        logger.info(log_entry)
+        # --- Step 7: Log the final result ---
+        if "Successfully" in result_message:
+            # On success, log the specific format you requested.
+            log_entry = (
+                f"This is an AI-generated documentation update for PR #{pr_number}, "
+                f"originally authored by @{user_name}.\n"
+                f"Original PR: '{pr_title}' AI Analysis: {analysis_summary}"
+            )
+            logger.info(log_entry)
+        else:
+            # On failure, log a simpler error message for clarity.
+            logger.error(
+                f"AGENT FAILED for PR #{pr_number} ({repo_name}). Reason: {result_message}"
+            )
 
     except Exception as e:
         logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
```