

---

### AI-Generated Update (2025-11-16 13:23:23)

```python
# --- 3. The "Creator" Chain (NEW) ---

def get_creator_chain():
    """
    Returns a chain that creates a NEW documentation section from scratch
    when no existing documentation is found.
    """
    system_prompt = """
    You are an expert technical writer tasked with creating a new documentation
    section for a feature that has no prior documentation.

    You will be given:
    1. A 'git diff' of the new code.
    2. An AI-generated analysis of what changed.
```

---

*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.

---

### Relevant Code Changes
```diff
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index a129961..7453050 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -10,7 +10,8 @@
     get_analyzer_chain, 
     get_rewriter_chain, 
     format_docs_for_context,
-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
+    get_summarizer_chain,
+    get_creator_chain
 )
 from vector_store import get_retriever, add_docs_to_store
 
@@ -23,11 +24,12 @@
     retriever = get_retriever()
     analyzer_chain = get_analyzer_chain()
     rewriter_chain = get_rewriter_chain()
-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
+    creator_chain = get_creator_chain()
+    summarizer_chain = get_summarizer_chain()
     print("✅ AI components are ready.")
 except Exception as e:
     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
-    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
+    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
 
 # --- GitHub PR Creation Logic (Synchronous) ---
 def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # --- Step 3: Retrieve relevant old docs ---
         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
         # Use `aget_relevant_documents` which returns scores with FAISS
-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
+        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
+            analysis_summary, k=5
+        )
         
-        # --- THIS IS THE FIX ---
-        # The score is in the metadata when using FAISS with similarity_score_threshold
-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
+        retrieved_docs = [doc for doc, score in docs_with_scores]
+        scores = [score for doc, score in docs_with_scores]
         
         # Calculate confidence score (highest similarity)
         confidence_score = max(scores) if scores else 0.0
         confidence_percent = f"{confidence_score * 100:.1f}%"
 
         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
-        
-        if not retrieved_docs:
-            await broadcaster("log-skip", "No relevant docs found to update.")
-            return
-        
-        if confidence_score < 0.5: # Gatekeeping based on confidence
-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
-            return
-        old_docs_context = format_docs_for_context(retrieved_docs)
 
-        # --- Step 4: Rewrite the docs ---
-        await broadcaster("log-step", "Generating new documentation with LLM...")
-        new_documentation = await rewriter_chain.ainvoke({
-            "analysis_summary": analysis_summary,
-            "old_docs_context": old_docs_context,
-            "git_diff": git_diff
-        })
+        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
+        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
+        pr_body_note = ""
+
+        if not retrieved_docs or confidence_score < confidence_threshold:
+            # CREATE MODE: No relevant docs found or confidence is too low.
+            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+            new_documentation = await creator_chain.ainvoke({
+                "analysis_summary": analysis_summary,
+                "git_diff": git_diff
+            })
+            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+            if confidence_score > 0:
+                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
+        else:
+            # UPDATE MODE: High confidence, proceed with rewriting.
+            await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
+            old_docs_context = format_docs_for_context(retrieved_docs)
+            new_documentation = await rewriter_chain.ainvoke({
+                "analysis_summary": analysis_summary,
+                "old_docs_context": old_docs_context,
+                "git_diff": git_diff
+            })
+            raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
         
         await broadcaster("log-step", "✅ New documentation generated.")
         
@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
+        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             "new_content": new_documentation,
             "source_files": source_files,
             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
+            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
+                        f"**Confidence Score:** {confidence_percent}\n\n"
+                        f"{pr_body_note}\n\n"
+                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
         }
 
         # --- Step 8: Create the GitHub PR ---
diff --git a/backend/llm_clients.py b/backend/llm_clients.py
index 0213b43..80fa1ee 100644
--- a/backend/llm_clients.py
+++ b/backend/llm_clients.py
@@ -188,7 +188,7 @@ def get_summarizer_chain():
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 4. The "Seeder" Chain (NEW) ---
+# --- 5. The "Seeder" Chain (NEW) ---
 
 def get_seeder_chain():
     """
```
