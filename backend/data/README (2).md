#### Main Execution Block (`if __name__ == "__main__":`)

This block runs the interactive console application.

---

1.  **Setup:** Loads environment variables (specifically `GEMINI_API_KEY`) and initializes the `ChatGoogleGenerativeAI` model (`gemini-1.5-flash`).
2.  **Component Initialization:** Creates instances of the core components from the `src` package: `EmbeddingPipeline`, `VectorStore`, and `RAGRetriever`.
3.  **Data Ingestion:**
    *   Checks if the vector store is already populated.
    *   If not, it loads all documents from the `data/text_files` directory.
    *   Uses the `EmbeddingPipeline` to process and embed the documents and adds them to the `VectorStore`.
4.  **Interactive Console Loop:**
    *   Starts an infinite `while` loop, prompting the user for a question.
    *   Listens for special commands: `exit`/`quit` to terminate and `reset` to clear the conversation history.
    *   The user's query is passed to `enhance_query_with_ai`.
    *   The (potentially enhanced) query is then passed to `rag_advanced` along with the current conversation history.

---

### 4. How to Run the Project

#### Prerequisites

Ensure you have Python installed and the required packages from `requirements.txt` (listed below).

# Expected Output

--- Starting RAG Pipeline Orchestration ---
✅ LLM initialized (gemini-1.5-flash)

--- INGESTION: Starting Document Loading and Indexing ---
--- INGESTION COMPLETE ---

--- Giva-Powered RAG Console Ready ---
🤖 Enhanced with giva conversation memory and intelligent document analysis
Commands: 'exit'/'quit' to close, 'reset' to clear conversation history
Ask questions about your documents for intelligent AI-powered answers!

Ask a question about your documents (or type 'exit'):

# Subsequent Runs & Interaction:

Ask a question about your documents (or type 'exit'): What is the project about?
🔍 Searching and generating answer...


🤖 GIVA-POWERED RAG RESPONSE

📝 QUESTION: What is the project about?
🎯 CONFIDENCE: 0.8123 (High)
📚 DOCUMENTS ANALYZED: 5

💡 GIVA ANSWER:

---
### Relevant Code Changes
```diff
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 1a12a16..4484b9a 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -1,5 +1,6 @@
 import os
 import asyncio
+import logging
 from github import Github
 from langchain_core.documents import Document
 
@@ -25,12 +26,12 @@
     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
     retriever, analyzer_chain, rewriter_chain = None, None, None
 
-# --- GitHub PR Creation Logic ---
+# --- GitHub PR Creation Logic (Synchronous) ---
+def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+    """Creates a new branch, updates files, and opens a pull request. (BLOCKING)"""
+    # Get a logger instance within the thread to ensure it's configured
+    logger = logging.getLogger(__name__)
 
-async def create_github_pr(repo_name, pr_number, pr_title, pr_body, source_files, new_content):
-    """
-    Creates a new branch, updates files, and opens a pull request.
-    """
     if not GITHUB_API_TOKEN:
         return "Error: GITHUB_API_TOKEN not set."
 
@@ -53,7 +54,7 @@ async def create_github_pr(repo_name, pr_number, pr_title, pr_body, source_files
             )
         except Exception as e:
             if "Reference already exists" in str(e):
-                print(f"Branch '{new_branch_name}' already exists. Proceeding...")
+                logger.info(f"Branch '{new_branch_name}' already exists. Proceeding...")
             else:
                 raise e
 
@@ -74,20 +75,20 @@ async def create_github_pr(repo_name, pr_number, pr_title, pr_body, source_files
                     sha=contents.sha,
                     branch=new_branch_name
                 )
-                print(f"Updated file: {file_path}")
+                logger.info(f"Successfully updated file: {file_path}")
                 files_updated_count += 1
             except Exception as e:
-                print(f"Failed to update file {file_path}: {e}. Skipping...")
+                logger.warning(f"Failed to update file {file_path}: {e}. Skipping...")
 
         # 6. Create the Pull Request
         if files_updated_count == 0:
-            print("No files were successfully updated, skipping PR creation.")
+            logger.warning("No files were successfully updated, skipping PR creation.")
             return "Error: No files were updated, so no PR was created."
 
         pr = repo.create_pull(
             title=pr_title,
             body=pr_body,
-            head=new_branch_name,      # The new branch
+            head=new_branch_name,
             base=repo.default_branch  # The branch to merge into
         )
         
@@ -95,17 +96,24 @@ async def create_github_pr(repo_name, pr_number, pr_title, pr_body, source_files
         return pr.html_url
 
     except Exception as e:
-        print(f"Error creating GitHub PR: {e}")
+        logger.error(f"Error creating GitHub PR: {e}", exc_info=True)
         return f"Error: {e}"
 
+# --- Async Wrapper for GitHub PR Creation ---
+async def create_github_pr_async(*args, **kwargs):
+    """
+    Runs the synchronous GitHub PR creation function in a separate thread
+    to avoid blocking the asyncio event loop.
+    """
+    # Use asyncio.to_thread which correctly handles passing kwargs to the thread.
+    # This is the modern replacement for loop.run_in_executor for this use case.
+    pr_url = await asyncio.to_thread(_create_github_pr_sync, *args, **kwargs)
+    return pr_url
 
 # --- Updated Core Agent Logic ---
 
-async def run_agent_analysis(broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: int):
-    """
-    This is the main "brain" of the agent. It runs the full
-    analysis-retrieval-rewrite pipeline.
-    """
+async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: int, user_name: str):
+    """This is the main 'brain' of the agent. It runs the full analysis-retrieval-rewrite pipeline."""
     
     if not retriever:
         print("Agent failed: AI components are not initialized.")
@@ -169,32 +177,60 @@ async def run_agent_analysis(broadcaster, git_diff: str, pr_title: str, repo_nam
             "new_content": new_documentation,
             "source_files": source_files,
             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
-            "pr_body": f"This is an AI-generated documentation update based on the changes in PR #{pr_number}.\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
+            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
         }
 
         # --- Step 6: Create the GitHub PR ---
         await broadcaster("log-step", "Attempting to create GitHub pull request...")
         
-        pr_url = await create_github_pr(
-            repo_name=repo_name,
-            pr_number=pr_number,
-            pr_title=pr_data["pr_title"],
-            pr_body=pr_data["pr_body"],
-            source_files=pr_data["source_files"],
-            new_content=pr_data["new_content"]
-        )
+        try:
+            pr_url = await create_github_pr_async(
+                repo_name=repo_name,
+                logger=logger,
+                pr_number=pr_number,
+                pr_title=pr_data["pr_title"],
+                pr_body=pr_data["pr_body"],
+                source_files=pr_data["source_files"],
+                new_content=pr_data["new_content"]
+            )
 
-        if "Error" in pr_url:
-            await broadcaster("log-error", f"Failed to create PR: {pr_url}")
-        else:
-            await broadcaster("log-action", f"✅ Successfully created PR: {pr_url}")
+            if "Error" in pr_url:
+                result_message = f"Failed to create PR. Reason: {pr_url}"
+                await broadcaster("log-error", f"Failed to create PR: {pr_url}")
+            else:
+                result_message = f"Successfully created documentation PR: {pr_url}"
+                await broadcaster("log-action", f"✅ Successfully created PR: {pr_url}")
+
+        except Exception as e:
+            result_message = f"Agent failed during PR creation with error: {e}"
+            await broadcaster("log-error", f"Agent failed with error: {e}")
+            # Log the exception traceback for debugging
+            logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
+
+        # --- Step 7: Create and write the detailed log entry ---
+        log_entry = f"""
+======================================================================
+AGENT RUN FOR PR #{pr_number}
+----------------------------------------------------------------------
+Repository:          {repo_name}
+Author:              @{user_name}
+Original PR Title:   '{pr_title}'
+AI Analysis:         {analysis_summary}
+---
+Generated Documentation:
+{new_documentation}
+---
+Result: {result_message}
+======================================================================
+"""
+        logger.info(log_entry)
 
     except Exception as e:
-        print(f"🔥 AGENT ERROR: {e}")
+        logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
         await broadcaster("log-error", f"Agent failed with error: {e}")
         return
 
 # --- Self-Test ---
 if __name__ == "__main__":
     print("This file is not meant to be run directly.")
-    print("Please run 'uvicorn main:app --reload' from the 'backend' directory.")
\ No newline at end of file
+    print("Please run 'uvicorn main:app --reload' from the 'backend' directory.")
```