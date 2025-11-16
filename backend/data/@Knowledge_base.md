

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


---

### AI-Generated Update (2025-11-16 14:24:06)

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
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
new file mode 100644
index 0000000..4fb803e
--- /dev/null
+++ b/backend/data/@Knowledge_base.md
@@ -0,0 +1,162 @@
+
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
++    get_summarizer_chain,
++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
++    creator_chain = get_creator_chain()
++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+-    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
++            analysis_summary, k=5
++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
++        retrieved_docs = [doc for doc, score in docs_with_scores]
++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+ 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
++        pr_body_note = ""
++
++        if not retrieved_docs or confidence_score < confidence_threshold:
++            # CREATE MODE: No relevant docs found or confidence is too low.
++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
++            new_documentation = await creator_chain.ainvoke({
++                "analysis_summary": analysis_summary,
++                "git_diff": git_diff
++            })
++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
++            if confidence_score > 0:
++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
++        else:
++            # UPDATE MODE: High confidence, proceed with rewriting.
++            await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
++            old_docs_context = format_docs_for_context(retrieved_docs)
++            new_documentation = await rewriter_chain.ainvoke({
++                "analysis_summary": analysis_summary,
++                "old_docs_context": old_docs_context,
++                "git_diff": git_diff
++            })
++            raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+         await broadcaster("log-step", "✅ New documentation generated.")
+         
+@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # The agent now "remembers" what it wrote by adding it to the central guide.
+         await update_knowledge_base(logger, broadcaster, new_documentation)
+ 
+-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
+-        # Instead of rebuilding, we add the new doc directly to the index.
++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
+         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
+         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
+         await asyncio.to_thread(add_docs_to_store, [new_doc])
+@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             "new_content": new_documentation,
+             "source_files": source_files,
+             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
+-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
++            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
++                        f"**Confidence Score:** {confidence_percent}\n\n"
++                        f"{pr_body_note}\n\n"
++                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
+         }
+ 
+         # --- Step 8: Create the GitHub PR ---
+diff --git a/backend/llm_clients.py b/backend/llm_clients.py
+index 0213b43..80fa1ee 100644
+--- a/backend/llm_clients.py
++++ b/backend/llm_clients.py
+@@ -188,7 +188,7 @@ def get_summarizer_chain():
+     summarizer_chain = prompt | llm | StrOutputParser()
+     return summarizer_chain
+ 
+-# --- 4. The "Seeder" Chain (NEW) ---
++# --- 5. The "Seeder" Chain (NEW) ---
+ 
+ def get_seeder_chain():
+     """
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 698e207..02e12e0 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1448,3 +1448,288 @@ Traceback (most recent call last):
   File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\prompts\base.py", line 181, in _validate_input
     raise KeyError(
 KeyError: "Input to ChatPromptTemplate is missing variables {'impact_description', 'file_name'}.  Expected: ['analysis_summary', 'file_name', 'git_diff', 'impact_description', 'user_name'] Received: ['user_name', 'analysis_summary', 'git_diff']\nNote: if you intended {impact_description} to be part of the string and not a variable, please escape it with double curly braces like: '{{impact_description}}'.\nFor troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/INVALID_PROMPT_INPUT "
+2025-11-16 13:23:23,410 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 13:23:32,602 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 13:23:34,356 - Successfully updated file: backend/llm_clients.py
+2025-11-16 13:23:36,450 - This is an AI-generated documentation update for PR #5fb8445, originally authored by @livingcool.
+Original PR: 'Push to main: updating major logic change' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
+2025-11-16 13:24:30,292 - Retrying langchain_google_genai.chat_models._achat_with_retry.<locals>._achat_with_retry in 2.0 seconds as it raised ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 29.467876197s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 29
+}
+].
+2025-11-16 13:24:34,920 - Retrying langchain_google_genai.chat_models._achat_with_retry.<locals>._achat_with_retry in 2.0 seconds as it raised ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 24.849079498s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 24
+}
+].
+2025-11-16 13:24:47,685 - Agent failed for PR #633bfce (livingcool/doc-ops-agent) with error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 12.084131612s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 12
+}
+]
+Traceback (most recent call last):
+  File "E:\2025\AI Learnings\GenAI Buildathon Sprint by Product Space\doc-ops-agent\backend\agent_logic.py", line 162, in run_agent_analysis
+    analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\runnables\base.py", line 3291, in ainvoke
+    input_ = await coro_with_context(part(), context, create_task=True)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 417, in ainvoke
+    llm_result = await self.agenerate_prompt(
+                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1036, in agenerate_prompt
+    return await self.agenerate(
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 994, in agenerate
+    raise exceptions[0]
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1164, in _agenerate_with_cache
+    result = await self._agenerate(
+             ^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 1010, in _agenerate
+    response: GenerateContentResponse = await _achat_with_retry(
+                                        ^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 229, in _achat_with_retry
+    return await _achat_with_retry(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 189, in async_wrapped
+    return await copy(fn, *args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 111, in __call__
+    do = await self.iter(retry_state=retry_state)
+         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 153, in iter
+    result = await action(retry_state)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\_utils.py", line 99, in inner
+    return call(*args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 420, in exc_check
+    raise retry_exc.reraise()
+          ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 187, in reraise
+    raise self.last_attempt.result()
+          ^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 449, in result
+    return self.__get_result()
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 401, in __get_result
+    raise self._exception
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 114, in __call__
+    result = await fn(*args, **kwargs)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 227, in _achat_with_retry
+    raise e
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 220, in _achat_with_retry
+    return await generation_method(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\async_client.py", line 440, in generate_content
+    response = await rpc(
+               ^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 231, in retry_wrapped_func
+    return await retry_target(
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 163, in retry_target
+    next_sleep = _retry_error_helper(
+                 ^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper
+    raise final_exc from source_exc
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 158, in retry_target
+    return await target()
+           ^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\grpc_helpers_async.py", line 89, in __await__
+    raise exceptions.from_grpc_error(rpc_error) from rpc_error
+google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 12.084131612s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 12
+}
+]
+2025-11-16 13:24:52,813 - Agent failed for PR #84 (livingcool/doc-ops-agent) with error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 6.953138473s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 6
+}
+]
+Traceback (most recent call last):
+  File "E:\2025\AI Learnings\GenAI Buildathon Sprint by Product Space\doc-ops-agent\backend\agent_logic.py", line 162, in run_agent_analysis
+    analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\runnables\base.py", line 3291, in ainvoke
+    input_ = await coro_with_context(part(), context, create_task=True)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 417, in ainvoke
+    llm_result = await self.agenerate_prompt(
+                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1036, in agenerate_prompt
+    return await self.agenerate(
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 994, in agenerate
+    raise exceptions[0]
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1164, in _agenerate_with_cache
+    result = await self._agenerate(
+             ^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 1010, in _agenerate
+    response: GenerateContentResponse = await _achat_with_retry(
+                                        ^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 229, in _achat_with_retry
+    return await _achat_with_retry(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 189, in async_wrapped
+    return await copy(fn, *args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 111, in __call__
+    do = await self.iter(retry_state=retry_state)
+         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 153, in iter
+    result = await action(retry_state)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\_utils.py", line 99, in inner
+    return call(*args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 420, in exc_check
+    raise retry_exc.reraise()
+          ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 187, in reraise
+    raise self.last_attempt.result()
+          ^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 449, in result
+    return self.__get_result()
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 401, in __get_result
+    raise self._exception
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 114, in __call__
+    result = await fn(*args, **kwargs)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 227, in _achat_with_retry
+    raise e
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 220, in _achat_with_retry
+    return await generation_method(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\async_client.py", line 440, in generate_content
+    response = await rpc(
+               ^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 231, in retry_wrapped_func
+    return await retry_target(
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 163, in retry_target
+    next_sleep = _retry_error_helper(
+                 ^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper
+    raise final_exc from source_exc
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 158, in retry_target
+    return await target()
+           ^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\grpc_helpers_async.py", line 89, in __await__
+    raise exceptions.from_grpc_error(rpc_error) from rpc_error
+google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 6.953138473s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 6
+}
+]
diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
index a7e6a44..31c8c55 100644
Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
index 3525f7c..f422459 100644
Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
diff --git a/backend/llm_clients.py b/backend/llm_clients.py
index 80fa1ee..fa5eb91 100644
--- a/backend/llm_clients.py
+++ b/backend/llm_clients.py
@@ -162,13 +162,13 @@ def get_summarizer_chain():
     Based on the provided analysis and git diff, produce a single sentence that
     describes the change and its impact.
 
-    Your response MUST be a single sentence in this exact format:
+    Your response MUST be a single sentence that follows the format:
     "A push by {user_name} to the file `<file_name>` has <impact_description>."
 
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
     - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that".
-    - Do not include line numbers.
-    - If multiple files are changed, pick the most important one.
+    - Do not include "from this to that" or line numbers.
     """
     
     prompt = ChatPromptTemplate.from_messages([
```


---

### AI-Generated Update (2025-11-16 14:34:57)

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
index 7453050..125ae6b 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
     with open(file_path, "a", encoding="utf-8") as f:
         f.write(content)
 
+def _extract_changed_lines(git_diff: str) -> str:
+    """A helper to extract only the added/modified lines from a git diff."""
+    changed_lines = []
+    for line in git_diff.split('\n'):
+        # We only care about lines that were added.
+        if line.startswith('+') and not line.startswith('+++'):
+            changed_lines.append(line[1:]) # Remove the '+'
+    
+    return "\n".join(changed_lines)
+
 # --- Updated Core Agent Logic ---
 
 async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
+        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
+        concise_diff = _extract_changed_lines(git_diff)
+        if not concise_diff:
+            await broadcaster("log-skip", "No functional code changes detected in diff.")
+            return
+
         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
-        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
         
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff # Use the concise diff here as well
         })
         # Broadcast the clean summary instead of the raw analysis
         await broadcaster("log-summary", human_readable_summary)
@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
             new_documentation = await creator_chain.ainvoke({
                 "analysis_summary": analysis_summary,
-                "git_diff": git_diff
+                "git_diff": concise_diff # Use the concise diff
             })
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
             if confidence_score > 0:
@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             new_documentation = await rewriter_chain.ainvoke({
                 "analysis_summary": analysis_summary,
                 "old_docs_context": old_docs_context,
-                "git_diff": git_diff
+                "git_diff": git_diff # The rewriter gets the full diff for context
             })
             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
         
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index 4fb803e..dcfa93c 100644
--- a/backend/data/@Knowledge_base.md
+++ b/backend/data/@Knowledge_base.md
@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
  def get_seeder_chain():
      """
 ```
+
+
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
+++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
+++    get_summarizer_chain,
+++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
+++    creator_chain = get_creator_chain()
+++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+-    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
+++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
+++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
+++            analysis_summary, k=5
+++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
+++        retrieved_docs = [doc for doc, score in docs_with_scores]
+++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
+++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
+++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
+++        pr_body_note = ""
+++
+++        if not retrieved_docs or confidence_score < confidence_threshold:
+++            # CREATE MODE: No relevant docs found or confidence is too low.
+++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+++            new_documentation = await creator_chain.ainvoke({
+++                "analysis_summary": analysis_summary,
+++                "git_diff": git_diff
+++            })
+++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+++            if confidence_score > 0:
+++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
+++        else:
+++            # UPDATE MODE: High confidence, proceed with rewriting.
+++            await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
+++            old_docs_context = format_docs_for_context(retrieved_docs)
+++            new_documentation = await rewriter_chain.ainvoke({
+++                "analysis_summary": analysis_summary,
+++                "old_docs_context": old_docs_context,
+++                "git_diff": git_diff
+++            })
+++            raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+         await broadcaster("log-step", "✅ New documentation generated.")
+         
+@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # The agent now "remembers" what it wrote by adding it to the central guide.
+         await update_knowledge_base(logger, broadcaster, new_documentation)
+ 
+-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
+-        # Instead of rebuilding, we add the new doc directly to the index.
+++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
+         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
+         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
+         await asyncio.to_thread(add_docs_to_store, [new_doc])
+@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             "new_content": new_documentation,
+             "source_files": source_files,
+             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
+-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
+++            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
+++                        f"**Confidence Score:** {confidence_percent}\n\n"
+++                        f"{pr_body_note}\n\n"
+++                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
+         }
+ 
+         # --- Step 8: Create the GitHub PR ---
+diff --git a/backend/llm_clients.py b/backend/llm_clients.py
+index 0213b43..80fa1ee 100644
+--- a/backend/llm_clients.py
+++++ b/backend/llm_clients.py
+@@ -188,7 +188,7 @@ def get_summarizer_chain():
+     summarizer_chain = prompt | llm | StrOutputParser()
+     return summarizer_chain
+ 
+-# --- 4. The "Seeder" Chain (NEW) ---
+++# --- 5. The "Seeder" Chain (NEW) ---
+ 
+ def get_seeder_chain():
+     """
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 02e12e0..378adde 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1733,3 +1733,149 @@ Please retry in 6.953138473s. [links {
   seconds: 6
 }
 ]
+2025-11-16 14:24:06,163 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 14:24:32,360 - Retrying langchain_google_genai.chat_models._achat_with_retry.<locals>._achat_with_retry in 2.0 seconds as it raised ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 27.43321765s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 27
+}
+].
+2025-11-16 14:24:55,686 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 14:25:14,647 - Retrying (GithubRetry(total=9, connect=None, read=None, redirect=None, status=None)) after connection broken by 'ReadTimeoutError("HTTPSConnectionPool(host='api.github.com', port=443): Read timed out. (read timeout=15)")': /repos/livingcool/doc-ops-agent/contents/backend/llm_clients.py
+2025-11-16 14:25:21,657 - Failed to update file backend/llm_clients.py: backend/llm_clients.py does not match fa5eb9192c0909d39555969a28b077ee41176443: 409 {"message": "backend/llm_clients.py does not match fa5eb9192c0909d39555969a28b077ee41176443", "documentation_url": "https://docs.github.com/rest/repos/contents#create-or-update-file-contents", "status": "409"}. Skipping...
+2025-11-16 14:25:25,218 - This is an AI-generated documentation update for PR #5f65ecd, originally authored by @livingcool.
+Original PR: 'Push to main: changes made in llm_client.py' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
+2025-11-16 14:25:40,773 - Agent failed for PR #cad4405 (livingcool/doc-ops-agent) with error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 19.003457153s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 19
+}
+]
+Traceback (most recent call last):
+  File "E:\2025\AI Learnings\GenAI Buildathon Sprint by Product Space\doc-ops-agent\backend\agent_logic.py", line 162, in run_agent_analysis
+    analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\runnables\base.py", line 3291, in ainvoke
+    input_ = await coro_with_context(part(), context, create_task=True)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 417, in ainvoke
+    llm_result = await self.agenerate_prompt(
+                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1036, in agenerate_prompt
+    return await self.agenerate(
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 994, in agenerate
+    raise exceptions[0]
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1164, in _agenerate_with_cache
+    result = await self._agenerate(
+             ^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 1010, in _agenerate
+    response: GenerateContentResponse = await _achat_with_retry(
+                                        ^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 229, in _achat_with_retry
+    return await _achat_with_retry(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 189, in async_wrapped
+    return await copy(fn, *args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 111, in __call__
+    do = await self.iter(retry_state=retry_state)
+         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 153, in iter
+    result = await action(retry_state)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\_utils.py", line 99, in inner
+    return call(*args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 420, in exc_check
+    raise retry_exc.reraise()
+          ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 187, in reraise
+    raise self.last_attempt.result()
+          ^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 449, in result
+    return self.__get_result()
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 401, in __get_result
+    raise self._exception
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 114, in __call__
+    result = await fn(*args, **kwargs)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 227, in _achat_with_retry
+    raise e
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 220, in _achat_with_retry
+    return await generation_method(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\async_client.py", line 440, in generate_content
+    response = await rpc(
+               ^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 231, in retry_wrapped_func
+    return await retry_target(
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 163, in retry_target
+    next_sleep = _retry_error_helper(
+                 ^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper
+    raise final_exc from source_exc
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 158, in retry_target
+    return await target()
+           ^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\grpc_helpers_async.py", line 89, in __await__
+    raise exceptions.from_grpc_error(rpc_error) from rpc_error
+google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 19.003457153s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 19
+}
+]
diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
index 31c8c55..7728838 100644
Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
index f422459..4556d9d 100644
Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ

```


---

### AI-Generated Update (2025-11-16 15:56:55)

# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store.
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
*   **Git**: [Download Git](https://git-scm.com/downloads/)
*   **GitHub Account**: You will need a personal GitHub account.
*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/livingcool/doc-ops-agent.git
    cd doc-ops-agent
    ```

2.  **Set up Backend Environment**:
    *   Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
        ```dotenv
        # .env file in backend/ directory
        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
        ```

3.  **Set up Frontend Environment**:
    *   Navigate to the `frontend/` directory:
        ```bash
        cd frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

4.  **Initialize the Vector Store**:
    *   Run the Python script to load initial documentation (if any) into the FAISS index:
        ```bash
        python ../backend/vector_store.py
        ```
        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.

## 5. Configuration

### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "DocSmith").
4.  Set the **Expiration** as needed (e.g., 90 days).
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
    *   `admin:repo_hook` (Full control of repository hooks)
6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.

### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.

### 5.3 Google AI API Key (`GOOGLE_API_KEY`)

1.  Log in to your Google AI Studio account.
2.  Go to the **API Key** section.
3.  Create a new API key or use an existing one.
4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.

### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)

This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.

## 6. Running the Application

1.  **Start the Backend Server**:
    *   Activate your backend virtual environment (`source venv/bin/activate`).
    *   Run the FastAPI application:
        ```bash
        cd backend
        uvicorn main:app --reload --port 8000
        ```

2.  **Start the Frontend Development Server**:
    *   Open a new terminal.
    *   Navigate to the `frontend/` directory.
    *   Run the React development server:
        ```bash
        cd frontend
        npm start
        ```
    *   The frontend will be available at `http://localhost:3000`.

3.  **Expose your Local Server with ngrok**:
    *   Open another terminal.
    *   Run ngrok to expose your local backend server to the internet:
        ```bash
        ngrok http 8000
        ```
    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).

4.  **Configure GitHub Webhook**:
    *   Go to your GitHub repository's **Settings** > **Webhooks**.
    *   Click **Add webhook**.
    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
    *   **Content type**: Select `application/json`.
    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
    *   Ensure **Active** is checked.
    *   Click **Add webhook**.

## 7. How to Use DocSmith

Your setup is complete! Now you can test DocSmith's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

---

You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.

## 8. Deployment to Render

To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.

1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
2.  **Configure the service** with the following settings:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

### AI-Generated Update (2025-11-16 14:34:57)

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
diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
index 629049c..a1e2d59 100644
--- a/backend/USER_GUIDE.md
+++ b/backend/USER_GUIDE.md
@@ -1,10 +1,10 @@
-# Doc-Ops Agent: User & Setup Guide
+# DocSmith: User & Setup Guide
 
-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
 
 ## 1. Overview
 
-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
 
 1.  **Analyzes the code diff** using an AI model (OpenAI).
 2.  **Determines if the change is significant** enough to warrant a documentation update.
@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
 
 ## 2. Core Technologies
 
-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
+*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
 *   **Frontend**: React, Server-Sent Events (SSE) for live logging
 *   **Vector Store**: FAISS for efficient similarity search
 
@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
 -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
 -   **Git**: [Download Git](https://git-scm.com/downloads/)
 -   **GitHub Account**: You will need a personal GitHub account.
--   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
+-   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
 -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
 
 ## 4. Setup and Installation
@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
     # Your GitHub Personal Access Token for API actions
     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
 
-    # Your OpenAI API key
-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
+    # Your Google AI API key for Gemini
+    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
 
     # (Optional) The minimum confidence score required to update a document
     CONFIDENCE_THRESHOLD=0.2
@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
 2.  Click **Generate new token** (or **Generate new token (classic)**).
-3.  Give it a descriptive name (e.g., "Doc-Ops Agent").
+3.  Give it a descriptive name (e.g., "DocSmith").
 4.  Set the **Expiration** as needed (e.g., 90 days).
 5.  Select the following **scopes**:
     *   `repo` (Full control of private repositories)
@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
 
-#### OpenAI API Key (`OPENAI_API_KEY`)
+#### Google AI API Key (`GOOGLE_API_KEY`)
 
 1.  Log in to your OpenAI Platform account.
 2.  Go to the **API Keys** section.
@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
 
 ## 8. How to Use the Agent
 
-Your setup is complete! Now you can test the agent's workflow.
+Your setup is complete! Now you can test DocSmith's workflow.
 
 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
-5.  **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
+5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
 6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
 
 ---
 
-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
 
 ## 9. Deployment to Render
 
-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
+To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
 
 1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
 2.  **Configure the service** with the following settings:
@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
     *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
         *   Use the port recommended by Render (e.g., `10000`).
  3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
-4.  **Deploy**: Trigger a manual deploy.
+4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
 
 Your agent is now live and will run automatically in the cloud!
\ No newline at end of file
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 125ae6b..6859d55 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -247,8 +247,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
         # --- Step 7: Package the results for the PR ---
         
-        # Get the raw source paths from metadata
-        raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+        # --- THIS IS THE FIX: Use the `raw_paths` determined in the Create/Update logic ---
         source_files = []
         for path in raw_paths:
             # 1. Fix Windows slashes
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index dcfa93c..28f6635 100644
--- a/backend/data/@Knowledge_base.md
+++ b/backend/data/@Knowledge_base.md
@@ -687,3 +687,438 @@ index 80fa1ee..fa5eb91 100644
      
      prompt = ChatPromptTemplate.from_messages([
 ```
+
+
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
++def _extract_changed_lines(git_diff: str) -> str:
++    """A helper to extract only the added/modified lines from a git diff."""
++    changed_lines = []
++    for line in git_diff.split('\n'):
++        # We only care about lines that were added.
++        if line.startswith('+') and not line.startswith('+++'):
++            changed_lines.append(line[1:]) # Remove the '+'
++    
++    return "\n".join(changed_lines)
++
+ # --- Updated Core Agent Logic ---
+ 
+ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
+@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+ 
+     try:
+         # --- Step 1: Analyze the code diff ---
++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++        concise_diff = _extract_changed_lines(git_diff)
++        if not concise_diff:
++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++            return
++
+         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
+-        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
+         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
+         
+         # --- NEW: Generate the clean, human-readable log message ---
+         human_readable_summary = await summarizer_chain.ainvoke({
+             "user_name": user_name,
+             "analysis_summary": analysis_summary,
+-            "git_diff": git_diff
++            "git_diff": concise_diff # Use the concise diff here as well
+         })
+         # Broadcast the clean summary instead of the raw analysis
+         await broadcaster("log-summary", human_readable_summary)
+@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+             new_documentation = await creator_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+-                "git_diff": git_diff
++                "git_diff": concise_diff # Use the concise diff
+             })
+             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+             if confidence_score > 0:
+@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             new_documentation = await rewriter_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+                 "old_docs_context": old_docs_context,
+-                "git_diff": git_diff
++                "git_diff": git_diff # The rewriter gets the full diff for context
+             })
+             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 4fb803e..dcfa93c 100644
+--- a/backend/data/@Knowledge_base.md
++++ b/backend/data/@Knowledge_base.md
+@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
+  def get_seeder_chain():
+      """
+ ```
++
++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
++++    get_summarizer_chain,
++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
++++    creator_chain = get_creator_chain()
++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
++++            analysis_summary, k=5
++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
++++        retrieved_docs = [doc for doc, score in docs_with_scores]
++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
++++        pr_body_note = ""
++++
++++        if not retrieved_docs or confidence_score < confidence_threshold:
++++            # CREATE MODE: No relevant docs found or confidence is too low.
++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
++++            new_documentation = await creator_chain.ainvoke({
++++                "analysis_summary": analysis_summary,
++++                "git_diff": git_diff
++++            })
++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
++++            if confidence_score > 0:
++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
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
+         
+         await broadcaster("log-step", "✅ New documentation generated.")
+         
+@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # The agent now "remembers" what it wrote by adding it to the central guide.
+         await update_knowledge_base(logger, broadcaster, new_documentation)
+ 
+-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
+-        # Instead of rebuilding, we add the new doc directly to the index.
++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
+         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
+         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
+         await asyncio.to_thread(add_docs_to_store, [new_doc])
+@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             "new_content": new_documentation,
+             "source_files": source_files,
+             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
+-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
++++            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
++++                        f"**Confidence Score:** {confidence_percent}\n\n"
++++                        f"{pr_body_note}\n\n"
++++                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
+         }
+ 
+         # --- Step 8: Create the GitHub PR ---
+diff --git a/backend/llm_clients.py b/backend/llm_clients.py
+index 0213b43..80fa1ee 100644
+--- a/backend/llm_clients.py
++++++ b/backend/llm_clients.py
+@@ -188,7 +188,7 @@ def get_summarizer_chain():
+     summarizer_chain = prompt | llm | StrOutputParser()
+     return summarizer_chain
+ 
+ -# --- 4. The "Seeder" Chain (NEW) ---
++++# --- 5. The "Seeder" Chain (NEW) ---
+ 
+ def get_seeder_chain():
+     """
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 02e12e0..378adde 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1733,3 +1733,149 @@ Please retry in 6.953138473s. [links {
   seconds: 6
 }
 ]
+2025-11-16 14:24:06,163 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 14:24:32,360 - Retrying langchain_google_genai.chat_models._achat_with_retry.<locals>._achat_with_retry in 2.0 seconds as it raised ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 27.43321765s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 27
+}
+].
+2025-11-16 14:24:55,686 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 14:25:14,647 - Retrying (GithubRetry(total=9, connect=None, read=None, redirect=None, status=None)) after connection broken by 'ReadTimeoutError("HTTPSConnectionPool(host='api.github.com', port=443): Read timed out. (read timeout=15)")': /repos/livingcool/doc-ops-agent/contents/backend/llm_clients.py
+2025-11-16 14:25:21,657 - Failed to update file backend/llm_clients.py: backend/llm_clients.py does not match fa5eb9192c0909d39555969a28b077ee41176443: 409 {"message": "backend/llm_clients.py does not match fa5eb9192c0909d39555969a28b077ee41176443", "documentation_url": "https://docs.github.com/rest/repos/contents#create-or-update-file-contents", "status": "409"}. Skipping...
+2025-11-16 14:25:25,218 - This is an AI-generated documentation update for PR #5f65ecd, originally authored by @livingcool.
+Original PR: 'Push to main: changes made in llm_client.py' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
+2025-11-16 14:25:40,773 - Agent failed for PR #cad4405 (livingcool/doc-ops-agent) with error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 19.003457153s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 19
+}
+]
+Traceback (most recent call last):
+  File "E:\2025\AI Learnings\GenAI Buildathon Sprint by Product Space\doc-ops-agent\backend\agent_logic.py", line 162, in run_agent_analysis
+    analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\runnables\base.py", line 3291, in ainvoke
+    input_ = await coro_with_context(part(), context, create_task=True)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 417, in ainvoke
+    llm_result = await self.agenerate_prompt(
+                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1036, in agenerate_prompt
+    return await self.agenerate(
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 994, in agenerate
+    raise exceptions[0]
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_core\language_models\chat_models.py", line 1164, in _agenerate_with_cache
+    result = await self._agenerate(
+             ^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 1010, in _agenerate
+    response: GenerateContentResponse = await _achat_with_retry(
+                                        ^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 229, in _achat_with_retry
+    return await _achat_with_retry(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 189, in async_wrapped
+    return await copy(fn, *args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 111, in __call__
+    do = await self.iter(retry_state=retry_state)
+         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 153, in iter
+    result = await action(retry_state)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\_utils.py", line 99, in inner
+    return call(*args, **kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 420, in exc_check
+    raise retry_exc.reraise()
+          ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\__init__.py", line 187, in reraise
+    raise self.last_attempt.result()
+          ^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 449, in result
+    return self.__get_result()
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py", line 401, in __get_result
+    raise self._exception
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\tenacity\asyncio\__init__.py", line 114, in __call__
+    result = await fn(*args, **kwargs)
+             ^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 227, in _achat_with_retry
+    raise e
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\langchain_google_genai\chat_models.py", line 220, in _achat_with_retry
+    return await generation_method(**kwargs)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\async_client.py", line 440, in generate_content
+    response = await rpc(
+               ^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 231, in retry_wrapped_func
+    return await retry_target(
+           ^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 163, in retry_target
+    next_sleep = _retry_error_helper(
+                 ^^^^^^^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper
+    raise final_exc from source_exc
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary_async.py", line 158, in retry_target
+    return await target()
+           ^^^^^^^^^^^^^^
+  File "C:\Users\ganes\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\grpc_helpers_async.py", line 89, in __await__
+    raise exceptions.from_grpc_error(rpc_error) from rpc_error
+google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
+* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 250000, model: gemini-2.5-flash
+Please retry in 19.003457153s. [links {
+  description: "Learn more about Gemini API quotas"
+  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
+}
+, violations {
+  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
+  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
+  quota_dimensions {
+    key: "model"
+    value: "gemini-2.5-flash"
+  }
+  quota_dimensions {
+    key: "location"
+    value: "global"
+  }
+  quota_value: 250000
+}
+, retry_delay {
+  seconds: 19
+}
+]
+diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
+index 31c8c55..7728838 100644
+Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
+diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
+index f422459..4556d9d 100644
+Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
+
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 378adde..1679431 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1879,3 +1879,8 @@ Please retry in 19.003457153s. [links {
   seconds: 19
 }
 ]
+2025-11-16 14:34:57,957 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 14:35:12,010 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 14:35:13,923 - Successfully updated file: backend/llm_clients.py
+2025-11-16 14:35:15,985 - This is an AI-generated documentation update for PR #a83ade0, originally authored by @livingcool.
+Original PR: 'Push to main: updated the logic' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
index 7728838..f15e01d 100644
Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
index 4556d9d..660ada7 100644
Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
diff --git a/backend/llm_clients.py b/backend/llm_clients.py
index fa5eb91..f9e7164 100644
--- a/backend/llm_clients.py
+++ b/backend/llm_clients.py
@@ -8,9 +8,17 @@
 # --- Load API Key ---
 load_dotenv()
 
+# Check if API key exists
+GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
+if not GOOGLE_API_KEY:
+    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
+
+# Set the API key for the SDK
+os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
+
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-2.5-flash", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
@@ -22,59 +30,57 @@ def get_analyzer_chain():
     """
     
     system_prompt = """
-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
-    and determine if the change is a 'trivial' change (like fixing a typo, 
-    adding comments, or refactoring code) or a 'functional' change 
-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
-
-    You MUST respond in JSON format with two keys:
-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
-
-    Examples:
-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
-    """
+You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
+and determine if the change is a 'trivial' change (like fixing a typo, 
+adding comments, or refactoring code) or a 'functional' change 
+(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+
+You MUST respond in JSON format with two keys:
+1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+
+Examples:
+- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+"""
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+""")
     ])
     
     return analyzer_chain
 
-# --- 2. The "Rewriter" Chain (UPDATED) ---
+# --- 2. The "Rewriter" Chain ---
 
 def get_rewriter_chain():
     """
     Returns a chain that rewrites documentation.
     """
     
-    # --- THIS PROMPT IS UPDATED ---
     system_prompt = """
-    You are an expert technical writer. Your task is to rewrite old documentation 
-    to match the new code changes.
+You are an expert technical writer. Your task is to rewrite old documentation 
+to match the new code changes.
 
-    You will be given:
-    1. The Old Documentation (as a list of relevant snippets).
-    2. The 'git diff' of the new code.
-    3. An analysis of what changed.
+You will be given:
+1. The Old Documentation (as a list of relevant snippets).
+2. The 'git diff' of the new code.
+3. An analysis of what changed.
 
-    Your job is to return the new, rewritten documentation.
-    - Maintain the original tone and formatting (e.g., Markdown).
-    - Do not add commentary like "Here is the new documentation:".
-    
-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
-    the relevant code diff. The final output must be in this format:
-    
-    [Your rewritten documentation text]
-    
-    ---
-    
-    ### Relevant Code Changes
-    ```diff
-    [The exact 'git diff' you were provided]
-    ```
-    """
-    # --- END OF UPDATE ---
+Your job is to return the new, rewritten documentation.
+- Maintain the original tone and formatting (e.g., Markdown).
+- Do not add commentary like "Here is the new documentation:".
+
+**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+the relevant code diff. The final output must be in this format:
+
+[Your rewritten documentation text]
+
+---
+
+### Relevant Code Changes
+```diff
+[The exact 'git diff' you were provided]
+```
+"""
     
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+""")
     ])
     
     # We pipe this to the LLM and then to a simple string parser
@@ -82,79 +88,79 @@ def get_rewriter_chain():
     
     return rewriter_chain
 
-# --- 3. The "Creator" Chain (NEW) ---
+# --- 3. The "Creator" Chain ---
 
 def get_creator_chain():
     """
     Returns a chain that creates a NEW documentation section from scratch
     when no existing documentation is found.
     """
-    system_prompt = """
-    You are an expert technical writer tasked with creating a new documentation
-    section for a feature that has no prior documentation.
-
-    You will be given:
-    1. A 'git diff' of the new code.
-    2. An AI-generated analysis of what changed.
-
-    Your job is to write a clear, concise documentation section explaining the new
-    feature. The output should be ready to be added to a larger document.
-    - Use Markdown formatting.
-    - Explain the feature's purpose and how it works based on the code.
-    - Do not add commentary like "Here is the new documentation:".
-    """
+    system_prompt = """You are an expert technical writer tasked with creating a new documentation
+section for a feature that has no prior documentation.
+
+You will be given:
+1. A 'git diff' of the new code.
+2. An AI-generated analysis of what changed.
+
+Your job is to write a clear, concise documentation section explaining the new
+feature. The output should be ready to be added to a larger document.
+- Use Markdown formatting.
+- Explain the feature's purpose and how it works based on the code.
+- Do not add commentary like "Here is the new documentation:".
+"""
     
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context for the new feature:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please write a new documentation section for this feature:
-        """)
+Here is the context for the new feature:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please write a new documentation section for this feature:
+""")
     ])
     
     creator_chain = prompt | llm | StrOutputParser()
     return creator_chain
 
-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
+# --- 4. The "Summarizer" Chain ---
 
 def get_summarizer_chain():
     """
     Returns a chain that creates a simple, human-readable summary of a change
-    for logging purposes, in the format you requested.
+    for logging purposes.
     """
     system_prompt = """
-    You are a technical project manager who writes concise, formal changelogs.
-    Based on the provided analysis and git diff, produce a single sentence that
-    describes the change and its impact.
+You are a technical project manager who writes concise, formal changelogs.
+Based on the provided analysis and git diff, produce a single sentence that
+describes the change and its impact.
 
-    Your response MUST be a single sentence that follows the format:
-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
+Your response MUST be a single sentence that follows the format:
+"A push by {user_name} to the file `<file_name>` has <impact_description>."
 
-    - You must determine the most relevant `<file_name>` from the git diff.
-    - You must write the `<impact_description>` based on the AI analysis.
-    - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that" or line numbers.
-    """
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
+    - Keep the `impact_description` brief and high-level.
+    - Do not include "from this to that" or line numbers.
+"""
     
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        CONTEXT:
-        - User: {user_name}
-        - AI Analysis: {analysis_summary}
-        - Git Diff:
-        ```diff
-        {git_diff}
-        ```
-        Please provide the single-sentence summary for the changelog:
-        """)
+CONTEXT:
+- User: {user_name}
+- AI Analysis: {analysis_summary}
+- Git Diff:
+```diff
+{git_diff}
+```
+Please provide the single-sentence summary for the changelog:
+""")
     ])
     
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 5. The "Seeder" Chain (NEW) ---
+# --- 5. The "Seeder" Chain ---
 
 def get_seeder_chain():
     """
@@ -162,31 +168,31 @@ def get_seeder_chain():
     to seed the knowledge base.
     """
     system_prompt = """
-    You are an expert technical writer tasked with creating a high-level project overview
-    to serve as the initial knowledge base for a software project.
+You are an expert technical writer tasked with creating a high-level project overview
+to serve as the initial knowledge base for a software project.
 
-    You will be given the concatenated source code of the project's key files.
+You will be given the concatenated source code of the project's key files.
 
-    Your job is to write a "README" style document that explains:
-    1.  What the project is and its main purpose.
-    2.  The core technologies used.
-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
+Your job is to write a "README" style document that explains:
+1. What the project is and its main purpose.
+2. The core technologies used.
+3. A brief explanation of how the main components work together.
 
-    The output should be in Markdown format and serve as a good starting point for project documentation.
-    Do not add commentary like "Here is the new documentation:".
-    """
+The output should be in Markdown format and serve as a good starting point for project documentation.
+Do not add commentary like "Here is the new documentation:".
+"""
     
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the source code of the project:
-        
-        ```python
-        {source_code}
-        ```
-        
-        Please generate the initial project documentation based on this code.
-        """)
+Here is the source code of the project:
+
+```python
+{source_code}
+```
+
+Please generate the initial project documentation based on this code.
+""")
     ])
     
     seeder_chain = prompt | llm | StrOutputParser()
@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
 # --- Self-Test ---
 if __name__ == "__main__":
     
-    print("--- Running LLM Clients Self-Test ---")
+    print("=" * 70)
+    print("Running Complete Doc-Ops LLM Chains Self-Test")
+    print("=" * 70)
+    
+    # Test data
+    test_diff_functional = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -10,5 +10,6 @@
+ @app.route('/api/v1/users')
+ def get_users():
+     return jsonify(users)
++
++@app.route('/api/v1/users/profile')
++def get_user_profile():
++    return jsonify({"name": "Test User", "status": "active"})
+"""
     
-    # 1. Test Analyzer Chain
-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
+    test_diff_trivial = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -1,3 +1,4 @@
+ # This file contains all API routes for our app.
+ from flask import Flask, jsonify
+
++# TODO: Add more routes later
+"""
+    
+    # 1. Test Analyzer Chain (Functional Change)
+    print("\n" + "-" * 70)
+    print("Test 1: Analyzer Chain (Functional Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_functional = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -10,5 +10,6 @@
-         @app.route('/api/v1/users')
-         def get_users():
-             return jsonify(users)
-        +
-        +@app.route('/api/v1/users/profile')
-        +def get_user_profile():
-        +    return jsonify({"name": "Test User", "status": "active"})
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_functional})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == True
-        print("Test Passed.")
+        print("✅ Test 1 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
+        print(f"❌ Test 1 Failed: {e}")
+        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
 
     # 2. Test Analyzer Chain (Trivial Change)
-    print("\n--- Testing Analyzer Chain (Trivial Change) ---")
+    print("\n" + "-" * 70)
+    print("Test 2: Analyzer Chain (Trivial Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_trivial = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -1,3 +1,3 @@
-         # This file contains all API routes for our app.
-         from flask import Flask, jsonify
-         
-         # TODO: Add more routes later
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_trivial})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == False
-        print("Test Passed.")
+        print("✅ Test 2 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
+        print(f"❌ Test 2 Failed: {e}")
 
     # 3. Test Rewriter Chain
-    print("\n--- Testing Rewriter Chain ---")
+    print("\n" + "-" * 70)
+    print("Test 3: Rewriter Chain")
+    print("-" * 70)
     try:
-        rewriter = get_rewriter_chain() # <-- Fixed typo
+        rewriter = get_rewriter_chain()
         test_old_docs = [
-            Document(page_content="Our API has one user endpoint: /api/v1/users.", metadata={"source": "api.md"})
+            Document(
+                page_content="Our API has one user endpoint: /api/v1/users.", 
+                metadata={"source": "api.md"}
+            )
         ]
         formatted_docs = format_docs_for_context(test_old_docs)
         
@@ -273,8 +293,76 @@ def get_users():
         })
         print(f"Response:\n{rewrite}")
         assert "/api/v1/users/profile" in rewrite
-        assert "Relevant Code Changes" in rewrite # Test new instruction
-        assert "--- a/api/routes.py" in rewrite # Test if diff is included
-        print("Test Passed.")
+        print("✅ Test 3 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
\ No newline at end of file
+        print(f"❌ Test 3 Failed: {e}")
+
+    # 4. Test Creator Chain
+    print("\n" + "-" * 70)
+    print("Test 4: Creator Chain (New Documentation)")
+    print("-" * 70)
+    try:
+        creator = get_creator_chain()
+        new_docs = creator.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{new_docs}")
+        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
+        print("✅ Test 4 Passed!")
+    except Exception as e:
+        print(f"❌ Test 4 Failed: {e}")
+
+    # 5. Test Summarizer Chain
+    print("\n" + "-" * 70)
+    print("Test 5: Summarizer Chain (Changelog)")
+    print("-" * 70)
+    try:
+        summarizer = get_summarizer_chain()
+        summary = summarizer.invoke({
+            "user_name": "john_doe",
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{summary}")
+        assert "john_doe" in summary or "api/routes.py" in summary
+        print("✅ Test 5 Passed!")
+    except Exception as e:
+        print(f"❌ Test 5 Failed: {e}")
+
+    # 6. Test Seeder Chain
+    print("\n" + "-" * 70)
+    print("Test 6: Seeder Chain (Initial Project Documentation)")
+    print("-" * 70)
+    try:
+        seeder = get_seeder_chain()
+        test_source_code = """
+from flask import Flask, jsonify
+
+app = Flask(__name__)
+
+@app.route('/api/v1/users')
+def get_users():
+    return jsonify({'users': ['Alice', 'Bob']})
+
+if __name__ == '__main__':
+    app.run(debug=True)
+"""
+        seed_docs = seeder.invoke({"source_code": test_source_code})
+        print(f"Response:\n{seed_docs}")
+        assert "Flask" in seed_docs or "API" in seed_docs
+        print("✅ Test 6 Passed!")
+    except Exception as e:
+        print(f"❌ Test 6 Failed: {e}")
+    
+    # Final Summary
+    print("\n" + "=" * 70)
+    print("Self-Test Complete!")
+    print("=" * 70)
+    print("\n💡 All chains are ready to use:")
+    print("   1. Analyzer Chain - Detects functional vs trivial changes")
+    print("   2. Rewriter Chain - Updates existing documentation")
+    print("   3. Creator Chain - Creates new documentation from scratch")
+    print("   4. Summarizer Chain - Generates changelog summaries")
+    print("   5. Seeder Chain - Creates initial project documentation")
+    print("=" * 70)
\ No newline at end of file
diff --git a/backend/main.py b/backend/main.py
index 7fecba5..de3dbe2 100644
--- a/backend/main.py
+++ b/backend/main.py
@@ -197,12 +197,12 @@ async def handle_github_webhook(
 # --- 3. Root Endpoint (for testing) ---
 @app.get("/")
 async def root():
-    return {"status": "Doc-Ops Agent is running"}
+    return {"status": "DocSmith is running"}
 
 # --- Run the server (for local testing) ---
 if __name__ == "__main__":
     import uvicorn
-    print("--- Starting Doc-Ops Agent Backend ---")
+    print("--- Starting DocSmith Backend ---")
     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
     print("--- AI Models are warming up... ---")
     uvicorn.run(app, host="0.0.0.0", port=8000)
\ No newline at end of file
diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
index eb531b5..df28c5f 100644
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -37,7 +37,7 @@ export default function App() {
   return (
     <div className="App">
       <header className="App-header">
-        <h1>Autonomous Doc-Ops Agent</h1>
+        <h1>DocSmith</h1>
         <div className="header-controls">
           <StatusBadge status={status} />
           <DarkModeToggle />

```


---

### AI-Generated Update (2025-11-16 17:31:28)

# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store.
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
*   **Git**: [Download Git](https://git-scm.com/downloads/)
*   **GitHub Account**: You will need a personal GitHub account.
*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/livingcool/doc-ops-agent.git
    cd doc-ops-agent
    ```

2.  **Set up Backend Environment**:
    *   Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
        ```dotenv
        # .env file in backend/ directory
        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
        ```

3.  **Set up Frontend Environment**:
    *   Navigate to the `frontend/` directory:
        ```bash
        cd frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

4.  **Initialize the Vector Store**:
    *   Run the Python script to load initial documentation (if any) into the FAISS index:
        ```bash
        python ../backend/vector_store.py
        ```
        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.

## 5. Configuration

### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "DocSmith").
4.  Set the **Expiration** as needed (e.g., 90 days).
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
    *   `admin:repo_hook` (Full control of repository hooks)
6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.

### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.

### 5.3 Google AI API Key (`GOOGLE_API_KEY`)

1.  Log in to your Google AI Studio account.
2.  Go to the **API Key** section.
3.  Create a new API key or use an existing one.
4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.

### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)

This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.

## 6. Running the Application

1.  **Start the Backend Server**:
    *   Activate your backend virtual environment (`source venv/bin/activate`).
    *   Run the FastAPI application:
        ```bash
        cd backend
        uvicorn main:app --reload --port 8000
        ```

2.  **Start the Frontend Development Server**:
    *   Open a new terminal.
    *   Navigate to the `frontend/` directory.
    *   Run the React development server:
        ```bash
        cd frontend
        npm start
        ```
    *   The frontend will be available at `http://localhost:3000`.

3.  **Expose your Local Server with ngrok**:
    *   Open another terminal.
    *   Run ngrok to expose your local backend server to the internet:
        ```bash
        ngrok http 8000
        ```
    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).

4.  **Configure GitHub Webhook**:
    *   Go to your GitHub repository's **Settings** > **Webhooks**.
    *   Click **Add webhook**.
    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
    *   **Content type**: Select `application/json`.
    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
    *   Ensure **Active** is checked.
    *   Click **Add webhook**.

## 7. How to Use DocSmith

Your setup is complete! Now you can test DocSmith's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

---

You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.

## 8. Deployment to Render

To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.

1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
2.  **Configure the service** with the following settings:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

## 9. Deployment (Frontend to Vercel)

To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.

1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
3.  **Configure Project**:
    *   Vercel will automatically detect that it's a Create React App.
    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
4.  **Configure Environment Variables**:
    *   This is the most important step. Expand the "Environment Variables" section.
    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.

---

You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!

---

### AI-Generated Update (2025-11-16 15:56:55)

# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store.
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
*   **Git**: [Download Git](https://git-scm.com/downloads/)
*   **GitHub Account**: You will need a personal GitHub account.
*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/livingcool/doc-ops-agent.git
    cd doc-ops-agent
    ```

2.  **Set up Backend Environment**:
    *   Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
        ```dotenv
        # .env file in backend/ directory
        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
        ```

3.  **Set up Frontend Environment**:
    *   Navigate to the `frontend/` directory:
        ```bash
        cd frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

4.  **Initialize the Vector Store**:
    *   Run the Python script to load initial documentation (if any) into the FAISS index:
        ```bash
        python ../backend/vector_store.py
        ```
        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.

## 5. Configuration

### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "DocSmith").
4.  Set the **Expiration** as needed (e.g., 90 days).
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
    *   `admin:repo_hook` (Full control of repository hooks)
6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.

### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.

### 5.3 Google AI API Key (`GOOGLE_API_KEY`)

1.  Log in to your Google AI Studio account.
2.  Go to the **API Key** section.
3.  Create a new API key or use an existing one.
4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.

### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)

This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.

## 6. Running the Application

1.  **Start the Backend Server**:
    *   Activate your backend virtual environment (`source venv/bin/activate`).
    *   Run the FastAPI application:
        ```bash
        cd backend
        uvicorn main:app --reload --port 8000
        ```

2.  **Start the Frontend Development Server**:
    *   Open a new terminal.
    *   Navigate to the `frontend/` directory.
    *   Run the React development server:
        ```bash
        cd frontend
        npm start
        ```
    *   The frontend will be available at `http://localhost:3000`.

3.  **Expose your Local Server with ngrok**:
    *   Open another terminal.
    *   Run ngrok to expose your local backend server to the internet:
        ```bash
        ngrok http 8000
        ```
    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).

4.  **Configure GitHub Webhook**:
    *   Go to your GitHub repository's **Settings** > **Webhooks**.
    *   Click **Add webhook**.
    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
    *   **Content type**: Select `application/json`.
    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
    *   Ensure **Active** is checked.
    *   Click **Add webhook**.

## 7. How to Use DocSmith

Your setup is complete! Now you can test DocSmith's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

---

You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.

## 8. Deployment to Render

To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.

1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
2.  **Configure the service** with the following settings:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

### AI-Generated Update (2025-11-16 14:34:57)

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
diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
index 629049c..a1e2d59 100644
--- a/backend/USER_GUIDE.md
++++ b/backend/USER_GUIDE.md
@@ -1,10 +1,10 @@
-# Doc-Ops Agent: User & Setup Guide
+# DocSmith: User & Setup Guide
 
-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
 
 ## 1. Overview
 
-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
 
 1.  **Analyzes the code diff** using an AI model (OpenAI).
 2.  **Determines if the change is significant** enough to warrant a documentation update.
@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
 
 ## 2. Core Technologies
 
-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
+*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
 *   **Frontend**: React, Server-Sent Events (SSE) for live logging
 *   **Vector Store**: FAISS for efficient similarity search
 
@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
 -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
 -   **Git**: [Download Git](https://git-scm.com/downloads/)
 -   **GitHub Account**: You will need a personal GitHub account.
--   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
+-   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
 -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
 
 ## 4. Setup and Installation
@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
     # Your GitHub Personal Access Token for API actions
     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
 
-    # Your OpenAI API key
-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
+    # Your Google AI API key for Gemini
+    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
 
     # (Optional) The minimum confidence score required to update a document
     CONFIDENCE_THRESHOLD=0.2
@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
 2.  Click **Generate new token** (or **Generate new token (classic)**).
--   Give it a descriptive name (e.g., "Doc-Ops Agent").
+-   Give it a descriptive name (e.g., "DocSmith").
  4.  Set the **Expiration** as needed (e.g., 90 days).
  5.  Select the following **scopes**:
      *   `repo` (Full control of private repositories)
@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
 
-#### OpenAI API Key (`OPENAI_API_KEY`)
+#### Google AI API Key (`GOOGLE_API_KEY`)
 
 1.  Log in to your OpenAI Platform account.
 2.  Go to the **API Keys** section.
@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
 
 ## 8. How to Use the Agent
 
-Your setup is complete! Now you can test the agent's workflow.
+Your setup is complete! Now you can test DocSmith's workflow.
 
 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
-5.  **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
+5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
 
  ---
 
-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
 
 ## 9. Deployment to Render
 
-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
+To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
 
  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
  2.  **Configure the service** with the following settings:
@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
          *   Use the port recommended by Render (e.g., `10000`).
   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
-4.  **Deploy**: Trigger a manual deploy.
+4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
 
  Your agent is now live and will run automatically in the cloud!
diff --git a/backend/agent_logic.py b/backend/agent_logic.py
index 125ae6b..6859d55 100644
--- a/backend/agent_logic.py
+++ b/backend/agent_logic.py
@@ -247,8 +247,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
         # --- Step 7: Package the results for the PR ---
         
-        # Get the raw source paths from metadata
-        raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+        # --- THIS IS THE FIX: Use the `raw_paths` determined in the Create/Update logic ---
         source_files = []
         for path in raw_paths:
             # 1. Fix Windows slashes
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index dcfa93c..28f6635 100644
--- a/backend/data/@Knowledge_base.md
+++ b/backend/data/@Knowledge_base.md
@@ -687,3 +687,438 @@ index 80fa1ee..fa5eb91 100644
      
      prompt = ChatPromptTemplate.from_messages([
 ```
+
+
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
+++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
+++def _extract_changed_lines(git_diff: str) -> str:
+++    """A helper to extract only the added/modified lines from a git diff."""
+++    changed_lines = []
+++    for line in git_diff.split('\n'):
+++        # We only care about lines that were added.
+++        if line.startswith('+') and not line.startswith('+++'):
+++            changed_lines.append(line[1:]) # Remove the '+'
+++    
+++    return "\n".join(changed_lines)
+++
++ # --- Updated Core Agent Logic ---
++ 
++ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
+@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+ 
+     try:
+         # --- Step 1: Analyze the code diff ---
+++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
+++        concise_diff = _extract_changed_lines(git_diff)
+++        if not concise_diff:
+++            await broadcaster("log-skip", "No functional code changes detected in diff.")
+++            return
+++
++         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
+-        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
+         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
+         
+         # --- NEW: Generate the clean, human-readable log message ---
+         human_readable_summary = await summarizer_chain.ainvoke({
+             "user_name": user_name,
+             "analysis_summary": analysis_summary,
+-            "git_diff": git_diff
+++            "git_diff": concise_diff # Use the concise diff here as well
+         })
+         # Broadcast the clean summary instead of the raw analysis
+         await broadcaster("log-summary", human_readable_summary)
+@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+             new_documentation = await creator_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+-                "git_diff": git_diff
+++                "git_diff": concise_diff # Use the concise diff
+             })
+             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+             if confidence_score > 0:
+@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             new_documentation = await rewriter_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+                 "old_docs_context": old_docs_context,
+-                "git_diff": git_diff
+++                "git_diff": git_diff # The rewriter gets the full diff for context
+             })
+             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 4fb803e..dcfa93c 100644
+--- a/backend/data/@Knowledge_base.md
+++++ b/backend/data/@Knowledge_base.md
+@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
+  def get_seeder_chain():
+      """
+ ```
+++
+++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
+++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
+++++    get_summarizer_chain,
+++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
+++++    creator_chain = get_creator_chain()
+++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
+++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
+++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
+++++            analysis_summary, k=5
+++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
+++++        retrieved_docs = [doc for doc, score in docs_with_scores]
+++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
+++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
+++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
+++++        pr_body_note = ""
+++++
+++++        if not retrieved_docs or confidence_score < confidence_threshold:
+++++            # CREATE MODE: No relevant docs found or confidence is too low.
+++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+++++            new_documentation = await creator_chain.ainvoke({
+++++                "analysis_summary": analysis_summary,
+++++                "git_diff": git_diff
+++++            })
+++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+++++            if confidence_score > 0:
+++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
+         else:
+             # UPDATE MODE: High confidence, proceed with rewriting.
+             await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
+             old_docs_context = format_docs_for_context(retrieved_docs)
+             new_documentation = await rewriter_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+                 "old_docs_context": old_docs_context,
+                 "git_diff": git_diff
+             })
+             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+         await broadcaster("log-step", "✅ New documentation generated.")
+         
+@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # The agent now "remembers" what it wrote by adding it to the central guide.
+         await update_knowledge_base(logger, broadcaster, new_documentation)
+ 
+-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
+-        # Instead of rebuilding, we add the new doc directly to the index.
+++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
+         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
+         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
+         await asyncio.to_thread(add_docs_to_store, [new_doc])
+@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             "new_content": new_documentation,
+             "source_files": source_files,
+             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
+-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
+++++            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
+++++                        f"**Confidence Score:** {confidence_percent}\n\n"
+++++                        f"{pr_body_note}\n\n"
+++++                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
+         }
+ 
+         # --- Step 8: Create the GitHub PR ---
+diff --git a/backend/llm_clients.py b/backend/llm_clients.py
+index 0213b43..80fa1ee 100644
+--- a/backend/llm_clients.py
+++++++ b/backend/llm_clients.py
+@@ -8,9 +8,17 @@
+ # --- Load API Key ---
+ load_dotenv()
+ 
++# Check if API key exists
++GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
++if not GOOGLE_API_KEY:
++    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
++
++# Set the API key for the SDK
++os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
++
+ # Initialize the Generative AI model
+ llm = ChatGoogleGenerativeAI(
+-    model="gemini-2.5-flash", 
++    model="gemini-2.5-flash-lite", 
+     temperature=0.2 
+ )
+ 
+@@ -22,59 +30,57 @@ def get_analyzer_chain():
+     """
+     
+     system_prompt = """
+-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
+-    and determine if the change is a 'trivial' change (like fixing a typo, 
+-    adding comments, or refactoring code) or a 'functional' change 
+-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+-
+-    You MUST respond in JSON format with two keys:
+-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+-
+-    Examples:
+-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+-    """
++You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
++and determine if the change is a 'trivial' change (like fixing a typo, 
++adding comments, or refactoring code) or a 'functional' change 
++(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
++
++You MUST respond in JSON format with two keys:
++1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
++2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
++   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
++
++Examples:
++- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
++- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
++- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
+ 
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        OLD DOCUMENTATION SNIPPETS:
+-        {old_docs_context}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please provide the new, updated documentation based on these changes:
+-        """)
++Here is the context:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++OLD DOCUMENTATION SNIPPETS:
++{old_docs_context}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please provide the new, updated documentation based on these changes:
+ """)
+     ])
+     
+     return analyzer_chain
+ 
+-# --- 2. The "Rewriter" Chain (UPDATED) ---
+-# --- 2. The "Rewriter" Chain ---
+ 
+ def get_rewriter_chain():
+     """
+     Returns a chain that rewrites documentation.
+     """
+     
+-    # --- THIS PROMPT IS UPDATED ---
+     system_prompt = """
+-    You are an expert technical writer. Your task is to rewrite old documentation 
+-    to match the new code changes.
++You are an expert technical writer. Your task is to rewrite old documentation 
++to match the new code changes.
+ 
+-    You will be given:
+-    1. The Old Documentation (as a list of relevant snippets).
+-    2. The 'git diff' of the new code.
+-    3. An analysis of what changed.
++You will be given:
++1. The Old Documentation (as a list of relevant snippets).
++2. The 'git diff' of the new code.
++3. An analysis of what changed.
+ 
+-    Your job is to return the new, rewritten documentation.
+-    - Maintain the original tone and formatting (e.g., Markdown).
+-    - Do not add commentary like "Here is the new documentation:".
+-    
+-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+-    the relevant code diff. The final output must be in this format:
+-    
+-    [Your rewritten documentation text]
+-    
+-    ---
+-    
+-    ### Relevant Code Changes
+-    ```diff
+-    [The exact 'git diff' you were provided]
+-    ```
+-    """
+-    # --- END OF UPDATE ---
++Your job is to return the new, rewritten documentation.
++- Maintain the original tone and formatting (e.g., Markdown).
++- Do not add commentary like "Here is the new documentation:".
++
++**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
++the relevant code diff. The final output must be in this format:
++
++[Your rewritten documentation text]
++
++---
++
++### Relevant Code Changes
++```diff
++[The exact 'git diff' you were provided]
++```
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        OLD DOCUMENTATION SNIPPETS:
+-        {old_docs_context}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please provide the new, updated documentation based on these changes:
+-        """)
++Here is the context:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++OLD DOCUMENTATION SNIPPETS:
++{old_docs_context}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please provide the new, updated documentation based on these changes:
+ """)
+     ])
+     
+     # We pipe this to the LLM and then to a simple string parser
+@@ -82,79 +88,79 @@ def get_rewriter_chain():
+     
+     return rewriter_chain
+ 
+-# --- 3. The "Creator" Chain (NEW) ---
++# --- 3. The "Creator" Chain ---
+ 
+ def get_creator_chain():
+     """
+     Returns a chain that creates a NEW documentation section from scratch
+     when no existing documentation is found.
+     """
+-    system_prompt = """
+-    You are an expert technical writer tasked with creating a new documentation
+-    section for a feature that has no prior documentation.
+-
+-    You will be given:
+-    1. A 'git diff' of the new code.
+-    2. An AI-generated analysis of what changed.
+-
+-    Your job is to write a clear, concise documentation section explaining the new
+-    feature. The output should be ready to be added to a larger document.
+-    - Use Markdown formatting.
+-    - Explain the feature's purpose and how it works based on the code.
+-    - Do not add commentary like "Here is the new documentation:".
+-    """
++    system_prompt = """You are an expert technical writer tasked with creating a new documentation
++section for a feature that has no prior documentation.
++
++You will be given:
++1. A 'git diff' of the new code.
++2. An AI-generated analysis of what changed.
++
++Your job is to write a clear, concise documentation section explaining the new
++feature. The output should be ready to be added to a larger document.
++- Use Markdown formatting.
++- Explain the feature's purpose and how it works based on the code.
++- Do not add commentary like "Here is the new documentation:".
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context for the new feature:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please write a new documentation section for this feature:
+-        """)
++Here is the context for the new feature:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please write a new documentation section for this feature:
+ """)
+     ])
+     
+     creator_chain = prompt | llm | StrOutputParser()
+     return creator_chain
+ 
+-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
+-# --- 4. The "Summarizer" Chain ---
+ 
+ def get_summarizer_chain():
+     """
+     Returns a chain that creates a simple, human-readable summary of a change
+-    for logging purposes, in the format you requested.
++    for logging purposes.
+     """
+     system_prompt = """
+-    You are a technical project manager who writes concise, formal changelogs.
+-    Based on the provided analysis and git diff, produce a single sentence that
+-    describes the change and its impact.
++You are a technical project manager who writes concise, formal changelogs.
++Based on the provided analysis and git diff, produce a single sentence that
++describes the change and its impact.
+ 
+-    Your response MUST be a single sentence that follows the format:
+-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
++Your response MUST be a single sentence that follows the format:
++"A push by {user_name} to the file `<file_name>` has <impact_description>."
+ 
+-    - You must determine the most relevant `<file_name>` from the git diff.
+-    - You must write the `<impact_description>` based on the AI analysis.
+-    - Keep the `impact_description` brief and high-level.
+-    - Do not include "from this to that" or line numbers.
+-    """
++    - You must determine the most relevant `<file_name>` from the git diff.
++    - You must write the `<impact_description>` based on the AI analysis.
++    - Keep the `impact_description` brief and high-level.
++    - Do not include "from this to that" or line numbers.
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        CONTEXT:
+-        - User: {user_name}
+-        - AI Analysis: {analysis_summary}
+-        - Git Diff:
+-        ```diff
+-        {git_diff}
+-        ```
+-        Please provide the single-sentence summary for the changelog:
+-        """)
++CONTEXT:
++- User: {user_name}
++- AI Analysis: {analysis_summary}
++- Git Diff:
++```diff
++{git_diff}
++```
++Please provide the single-sentence summary for the changelog:
+ """)
+     ])
+     
+     summarizer_chain = prompt | llm | StrOutputParser()
+     return summarizer_chain
+ 
+-# --- 5. The "Seeder" Chain (NEW) ---
+-# --- 5. The "Seeder" Chain ---
+ 
+ def get_seeder_chain():
+     """
+@@ -162,31 +168,31 @@ def get_seeder_chain():
+     to seed the knowledge base.
+     """
+     system_prompt = """
+-    You are an expert technical writer tasked with creating a high-level project overview
+-    to serve as the initial knowledge base for a software project.
++You are an expert technical writer tasked with creating a high-level project overview
++to serve as the initial knowledge base for a software project.
+ 
+-    You will be given the concatenated source code of the project's key files.
++You will be given the concatenated source code of the project's key files.
+ 
+-    Your job is to write a "README" style document that explains:
+-    1.  What the project is and its main purpose.
+-    2.  The core technologies used.
+-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
++Your job is to write a "README" style document that explains:
++1. What the project is and its main purpose.
++2. The core technologies used.
++3. A brief explanation of how the main components work together.
+ 
+-    The output should be in Markdown format and serve as a good starting point for project documentation.
+-    Do not add commentary like "Here is the new documentation:".
+-    """
++The output should be in Markdown format and serve as a good starting point for project documentation.
++Do not add commentary like "Here is the new documentation:".
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the source code of the project:
+-        
+-        ```python
+-        {source_code}
+-        ```
+-        
+-        Please generate the initial project documentation based on this code.
+-        """)
++Here is the source code of the project:
++
++```python
++{source_code}
++```
++
++Please generate the initial project documentation based on this code.
+ """)
+     ])
+     
+     seeder_chain = prompt | llm | StrOutputParser()
+@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
+ # --- Self-Test ---
+ if __name__ == "__main__":
+     
+-    print("--- Running LLM Clients Self-Test ---")
++    print("=" * 70)
++    print("Running Complete Doc-Ops LLM Chains Self-Test")
++    print("=" * 70)
+     
+-    # Test data
+-    test_diff_functional = """
+-    --- a/api/routes.py
+++++ b/api/routes.py
++@@ -10,5 +10,6 @@
++ @app.route('/api/v1/users')
++ def get_users():
++     return jsonify(users)
+++
+++@app.route('/api/v1/users/profile')
+++def get_user_profile():
+++    return jsonify({"name": "Test User", "status": "active"})
++"""
+     
+-    # 1. Test Analyzer Chain
+-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
++    test_diff_trivial = """
++--- a/api/routes.py
+++++ b/api/routes.py
++@@ -1,3 +1,4 @@
++ # This file contains all API routes for our app.
++ from flask import Flask, jsonify
++
+++# TODO: Add more routes later
++"""
+     
+     # 1. Test Analyzer Chain (Functional Change)
+     print("\n" + "-" * 70)
+     print("Test 1: Analyzer Chain (Functional Change)")
+     print("-" * 70)
+     try:
+         analyzer = get_analyzer_chain()
+-        test_diff_functional = """
+-        --- a/api/routes.py
+-        +++ b/api/routes.py
+-        @@ -10,5 +10,6 @@
+-         @app.route('/api/v1/users')
+-         def get_users():
+-             return jsonify(users)
+-        +
+-        +@app.route('/api/v1/users/profile')
+-        +def get_user_profile():
+-        +    return jsonify({"name": "Test User", "status": "active"})
+-        """
+         analysis = analyzer.invoke({"git_diff": test_diff_functional})
+         print(f"Response:\n{analysis}")
+         assert analysis['is_functional_change'] == True
+-        print("Test Passed.")
++        print("✅ Test 1 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
+-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
++        print(f"❌ Test 1 Failed: {e}")
++        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+ 
+     # 2. Test Analyzer Chain (Trivial Change)
+-    print("\n--- Testing Analyzer Chain (Trivial Change) ---")
++    print("\n" + "-" * 70)
++    print("Test 2: Analyzer Chain (Trivial Change)")
++    print("-" * 70)
+     try:
+         analyzer = get_analyzer_chain()
+-        test_diff_trivial = """
+-        --- a/api/routes.py
+-        +++ b/api/routes.py
+-        @@ -1,3 +1,3 @@
+-         # This file contains all API routes for our app.
+-         from flask import Flask, jsonify
+-         
+-         # TODO: Add more routes later
+-        """
+         analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+         print(f"Response:\n{analysis}")
+         assert analysis['is_functional_change'] == False
+-        print("Test Passed.")
++        print("✅ Test 2 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
++        print(f"❌ Test 2 Failed: {e}")
+ 
+     # 3. Test Rewriter Chain
+-    print("\n--- Testing Rewriter Chain ---")
++    print("\n" + "-" * 70)
++    print("Test 3: Rewriter Chain")
++    print("-" * 70)
+     try:
+-        rewriter = get_rewriter_chain() # <-- Fixed typo
++        rewriter = get_rewriter_chain()
+         test_old_docs = [
+-            Document(page_content="Our API has one user endpoint: /api/v1/users.", metadata={"source": "api.md"})
++            Document(
++                page_content="Our API has one user endpoint: /api/v1/users.", 
++                metadata={"source": "api.md"}
++            )
+         ]
+         formatted_docs = format_docs_for_context(test_old_docs)
+         
+@@ -273,8 +293,76 @@ def get_users():
+         })
+         print(f"Response:\n{rewrite}")
+         assert "/api/v1/users/profile" in rewrite
+-        assert "Relevant Code Changes" in rewrite # Test new instruction
+-        assert "--- a/api/routes.py" in rewrite # Test if diff is included
+-        print("Test Passed.")
++        print("✅ Test 3 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
+\ No newline at end of file
+         print(f"❌ Test 3 Failed: {e}")
++
++    # 4. Test Creator Chain
++    print("\n" + "-" * 70)
++    print("Test 4: Creator Chain (New Documentation)")
++    print("-" * 70)
++    try:
++        creator = get_creator_chain()
++        new_docs = creator.invoke({
++            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
++            "git_diff": test_diff_functional
++        })
++        print(f"Response:\n{new_docs}")
++        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
++        print("✅ Test 4 Passed!")
+     except Exception as e:
++        print(f"❌ Test 4 Failed: {e}")
++
++    # 5. Test Summarizer Chain
++    print("\n" + "-" * 70)
++    print("Test 5: Summarizer Chain (Changelog)")
++    print("-" * 70)
++    try:
++        summarizer = get_summarizer_chain()
++        summary = summarizer.invoke({
++            "user_name": "john_doe",
++            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
++            "git_diff": test_diff_functional
++        })
++        print(f"Response:\n{summary}")
++        assert "john_doe" in summary or "api/routes.py" in summary
++        print("✅ Test 5 Passed!")
+     except Exception as e:
++        print(f"❌ Test 5 Failed: {e}")
++
++    # 6. Test Seeder Chain
++    print("\n" + "-" * 70)
++    print("Test 6: Seeder Chain (Initial Project Documentation)")
++    print("-" * 70)
++    try:
++        seeder = get_seeder_chain()
++        test_source_code = """
++from flask import Flask, jsonify
++
++app = Flask(__name__)
++
++@app.route('/api/v1/users')
++def get_users():
++    return jsonify({'users': ['Alice', 'Bob']})
++
++if __name__ == '__main__':
++    app.run(debug=True)
++"""
++        seed_docs = seeder.invoke({"source_code": test_source_code})
++        print(f"Response:\n{seed_docs}")
++        assert "Flask" in seed_docs or "API" in seed_docs
++        print("✅ Test 6 Passed!")
+     except Exception as e:
++        print(f"❌ Test 6 Failed: {e}")
++    
+     # Final Summary
+     print("\n" + "=" * 70)
+     print("Self-Test Complete!")
+     print("=" * 70)
+     print("\n💡 All chains are ready to use:")
+     print("   1. Analyzer Chain - Detects functional vs trivial changes")
+     print("   2. Rewriter Chain - Updates existing documentation")
+     print("   3. Creator Chain - Creates new documentation from scratch")
+     print("   4. Summarizer Chain - Generates changelog summaries")
+     print("   5. Seeder Chain - Creates initial project documentation")
+     print("=" * 70)
+\ No newline at end of file
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+\ No newline at end of file
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 1679431..73b3ae7 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1884,3 +1884,7 @@ Please retry in 19.003457153s. [links {
 2025-11-16 14:35:13,923 - Successfully updated file: backend/llm_clients.py
 2025-11-16 14:35:15,985 - This is an AI-generated documentation update for PR #a83ade0, originally authored by @livingcool.
 Original PR: 'Push to main: updated the logic' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
+2025-11-16 15:56:55,691 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 15:57:11,092 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 15:57:13,153 - This is an AI-generated documentation update for PR #7fc6e13, originally authored by @livingcool.
+Original PR: 'Push to main: Change the name of the application' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
index f15e01d..df4820a 100644
Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
index 660ada7..bd0b01d 100644
Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
index df28c5f..b4018b5 100644
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -11,7 +11,8 @@ import { LogIcon } from './components/LogIcon.jsx';
 
 import './App.css'; // Your component styles
 
-const BACKEND_STREAM_URL = "http://localhost:8000/api/stream/logs";
+const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
+const BACKEND_STREAM_URL = `${BACKEND_URL}/api/stream/logs`;
 
 export default function App() {
   const { logs, status } = useEventSource(BACKEND_STREAM_URL);
@@ -27,7 +28,7 @@ export default function App() {
         <LogIcon type="log-error" />
         <div className="log-message">
-          Could not connect to backend at <code>{BACKEND_STREAM_URL}</code>.
+          Could not connect to backend at <code>{BACKEND_URL}</code>.
           Is the FastAPI server running on port 8000?
         </div>
       </motion.div>

---

### Relevant Code Changes
```diff
diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
index 629049c..6fc069a 100644
--- a/backend/USER_GUIDE.md
+++ b/backend/USER_GUIDE.md
@@ -1,10 +1,10 @@
-# Doc-Ops Agent: User & Setup Guide
+# DocSmith: User & Setup Guide
 
-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
 
 ## 1. Overview
 
-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
 
 1.  **Analyzes the code diff** using an AI model (OpenAI).
 2.  **Determines if the change is significant** enough to warrant a documentation update.
@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
 
 ## 2. Core Technologies
 
-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
+*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
 *   **Frontend**: React, Server-Sent Events (SSE) for live logging
 *   **Vector Store**: FAISS for efficient similarity search
 
@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
 -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
 -   **Git**: [Download Git](https://git-scm.com/downloads/)
 -   **GitHub Account**: You will need a personal GitHub account.
--   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
+-   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
 -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
 
 ## 4. Setup and Installation
@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
     # Your GitHub Personal Access Token for API actions
     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
 
-    # Your OpenAI API key
-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
+    # Your Google AI API key for Gemini
+    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
 
     # (Optional) The minimum confidence score required to update a document
     CONFIDENCE_THRESHOLD=0.2
@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
 2.  Click **Generate new token** (or **Generate new token (classic)**).
--   Give it a descriptive name (e.g., "Doc-Ops Agent").
+-   Give it a descriptive name (e.g., "DocSmith").
  4.  Set the **Expiration** as needed (e.g., 90 days).
  5.  Select the following **scopes**:
      *   `repo` (Full control of private repositories)
@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
 
 This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
 
-#### OpenAI API Key (`OPENAI_API_KEY`)
+#### Google AI API Key (`GOOGLE_API_KEY`)
 
 1.  Log in to your OpenAI Platform account.
 2.  Go to the **API Keys** section.
@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
 
 ## 8. How to Use the Agent
 
-Your setup is complete! Now you can test the agent's workflow.
+Your setup is complete! Now you can test DocSmith's workflow.
 
 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
-5.  **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
+5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
 
  ---
 
-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
 
 ## 9. Deployment to Render
 
-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
+To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
 
  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
  2.  **Configure the service** with the following settings:
@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
          *   Use the port recommended by Render (e.g., `10000`).
   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
-4.  **Deploy**: Trigger a manual deploy.
+4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
 
  Your agent is now live and will run automatically in the cloud!
@@ -211,4 +211,23 @@ To deploy the backend to a persistent cloud service like Render, follow these st
  4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
 
-Your agent is now live and will run automatically in the cloud!
\ No newline at end of file
+Your agent is now live and will run automatically in the cloud!
+
+## 10. Deployment (Frontend to Vercel)
+
+To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.
+
+1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
+2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
+3.  **Configure Project**:
+    *   Vercel will automatically detect that it's a Create React App.
+    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
+4.  **Configure Environment Variables**:
+    *   This is the most important step. Expand the "Environment Variables" section.
+    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
+    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
+5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.
+
+---
+
+You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!
\ No newline at end of file
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index 28f6635..0e5420a 100644
--- a/backend/data/@Knowledge_base.md
+++ b/backend/data/@Knowledge_base.md
@@ -1122,3 +1122,1393 @@ index f422459..4556d9d 100644
 Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
 
 ```
+
+
+---
+
+### AI-Generated Update (2025-11-16 15:56:55)
+
+# DocSmith: User & Setup Guide
+
+Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+
+## 1. Overview
+
+DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+
+1.  **Analyzes the code diff** using an AI model (Google Gemini).
+2.  **Determines if the change is significant** enough to warrant a documentation update.
+3.  **Retrieves relevant existing documentation** snippets from a vector store.
+4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
+5.  **Creates a new pull request** with the documentation changes.
+
+## 2. Core Technologies
+
+*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
+*   **Frontend**: React, Server-Sent Events (SSE) for live logging
+*   **Vector Store**: FAISS for efficient similarity search
+
+## 3. Prerequisites
+
+Before you begin, ensure you have the following installed and configured:
+
+*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
+*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
+*   **Git**: [Download Git](https://git-scm.com/downloads/)
+*   **GitHub Account**: You will need a personal GitHub account.
+*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
+*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
+
+## 4. Setup and Installation
+
+1.  **Clone the Repository**:
+    ```bash
+    git clone https://github.com/livingcool/doc-ops-agent.git
+    cd doc-ops-agent
+    ```
+
+2.  **Set up Backend Environment**:
+    *   Create a virtual environment:
+        ```bash
+        python -m venv venv
+        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
+        ```
+    *   Install Python dependencies:
+        ```bash
+        pip install -r requirements.txt
+        ```
+    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
+        ```dotenv
+        # .env file in backend/ directory
+        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
+        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
+        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
+        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
+        ```
+
+3.  **Set up Frontend Environment**:
+    *   Navigate to the `frontend/` directory:
+        ```bash
+        cd frontend
+        ```
+    *   Install Node.js dependencies:
+        ```bash
+        npm install
+        ```
+
+4.  **Initialize the Vector Store**:
+    *   Run the Python script to load initial documentation (if any) into the FAISS index:
+        ```bash
+        python ../backend/vector_store.py
+        ```
+        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.
+
+## 5. Configuration
+
+### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)
+
+The agent needs this token to create branches and pull requests on your behalf.
+
+1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
+2.  Click **Generate new token** (or **Generate new token (classic)**).
+3.  Give it a descriptive name (e.g., "DocSmith").
+4.  Set the **Expiration** as needed (e.g., 90 days).
+5.  Select the following **scopes**:
+    *   `repo` (Full control of private repositories)
+    *   `admin:repo_hook` (Full control of repository hooks)
+6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.
+
+### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)
+
+This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.
+
+### 5.3 Google AI API Key (`GOOGLE_API_KEY`)
+
+1.  Log in to your Google AI Studio account.
+2.  Go to the **API Key** section.
+3.  Create a new API key or use an existing one.
+4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.
+
+### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)
+
+This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.
+
+## 6. Running the Application
+
+1.  **Start the Backend Server**:
+    *   Activate your backend virtual environment (`source venv/bin/activate`).
+    *   Run the FastAPI application:
+        ```bash
+        cd backend
+        uvicorn main:app --reload --port 8000
+        ```
+
+2.  **Start the Frontend Development Server**:
+    *   Open a new terminal.
+    *   Navigate to the `frontend/` directory.
+    *   Run the React development server:
+        ```bash
+        cd frontend
+        npm start
+        ```
+    *   The frontend will be available at `http://localhost:3000`.
+
+3.  **Expose your Local Server with ngrok**:
+    *   Open another terminal.
+    *   Run ngrok to expose your local backend server to the internet:
+        ```bash
+        ngrok http 8000
+        ```
+    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).
+
+4.  **Configure GitHub Webhook**:
+    *   Go to your GitHub repository's **Settings** > **Webhooks**.
+    *   Click **Add webhook**.
+    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
+    *   **Content type**: Select `application/json`.
+    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
+    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
+    *   Ensure **Active** is checked.
+    *   Click **Add webhook**.
+
+## 7. How to Use DocSmith
+
+Your setup is complete! Now you can test DocSmith's workflow.
+
+1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
+2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
+3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
+4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
+5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
+6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
+
+---
+
+You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+
+## 8. Deployment to Render
+
+To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
+
+1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
+2.  **Configure the service** with the following settings:
+    *   **Build Command**: `pip install -r requirements.txt`
+    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
+        *   Use the port recommended by Render (e.g., `10000`).
+3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
+4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+
+Your agent is now live and will run automatically in the cloud!
+
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
+++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
+++def _extract_changed_lines(git_diff: str) -> str:
+++    """A helper to extract only the added/modified lines from a git diff."""
+++    changed_lines = []
+++    for line in git_diff.split('\n'):
+++        # We only care about lines that were added.
+++        if line.startswith('+') and not line.startswith('+++'):
+++            changed_lines.append(line[1:]) # Remove the '+'
+++    
+++    return "\n".join(changed_lines)
+++
++ # --- Updated Core Agent Logic ---
++ 
++ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
+@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+ 
+     try:
+         # --- Step 1: Analyze the code diff ---
+++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
+++        concise_diff = _extract_changed_lines(git_diff)
+++        if not concise_diff:
+++            await broadcaster("log-skip", "No functional code changes detected in diff.")
+++            return
+++
++         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
+-        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
+++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
+         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
+         
+         # --- NEW: Generate the clean, human-readable log message ---
+         human_readable_summary = await summarizer_chain.ainvoke({
+             "user_name": user_name,
+             "analysis_summary": analysis_summary,
+-            "git_diff": git_diff
+++            "git_diff": concise_diff # Use the concise diff here as well
+         })
+         # Broadcast the clean summary instead of the raw analysis
+         await broadcaster("log-summary", human_readable_summary)
+@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+             new_documentation = await creator_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+-                "git_diff": git_diff
+++                "git_diff": concise_diff # Use the concise diff
+             })
+             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+             if confidence_score > 0:
+@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             new_documentation = await rewriter_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+                 "old_docs_context": old_docs_context,
+-                "git_diff": git_diff
+++                "git_diff": git_diff # The rewriter gets the full diff for context
+             })
+             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 4fb803e..dcfa93c 100644
+--- a/backend/data/@Knowledge_base.md
+++++ b/backend/data/@Knowledge_base.md
+@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
+  def get_seeder_chain():
+      """
+ ```
+++
+++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
+++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
+++++    get_summarizer_chain,
+++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
+++++    creator_chain = get_creator_chain()
+++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
+++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
+++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
+++++            analysis_summary, k=5
+++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
+++++        retrieved_docs = [doc for doc, score in docs_with_scores]
+++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
+++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
+++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
+++++        pr_body_note = ""
+++++
+++++        if not retrieved_docs or confidence_score < confidence_threshold:
+++++            # CREATE MODE: No relevant docs found or confidence is too low.
+++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
+++++            new_documentation = await creator_chain.ainvoke({
+++++                "analysis_summary": analysis_summary,
+++++                "git_diff": git_diff
+++++            })
+++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
+++++            if confidence_score > 0:
+++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
+         else:
+             # UPDATE MODE: High confidence, proceed with rewriting.
+             await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
+             old_docs_context = format_docs_for_context(retrieved_docs)
+             new_documentation = await rewriter_chain.ainvoke({
+                 "analysis_summary": analysis_summary,
+                 "old_docs_context": old_docs_context,
+                 "git_diff": git_diff
+             })
+             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
+         
+         await broadcaster("log-step", "✅ New documentation generated.")
+         
+@@ -212,8 +232,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # The agent now "remembers" what it wrote by adding it to the central guide.
+         await update_knowledge_base(logger, broadcaster, new_documentation)
+ 
+-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
+-        # Instead of rebuilding, we add the new doc directly to the index.
+++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
+         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
+         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
+         await asyncio.to_thread(add_docs_to_store, [new_doc])
+@@ -241,7 +260,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+             "new_content": new_documentation,
+             "source_files": source_files,
+             "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
+-            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Confidence Score:** {confidence_percent}\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
+++++            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
+++++                        f"**Confidence Score:** {confidence_percent}\n\n"
+++++                        f"{pr_body_note}\n\n"
+++++                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
+         }
+ 
+         # --- Step 8: Create the GitHub PR ---
+diff --git a/backend/llm_clients.py b/backend/llm_clients.py
+index 0213b43..80fa1ee 100644
+--- a/backend/llm_clients.py
+++++++ b/backend/llm_clients.py
+@@ -8,9 +8,17 @@
+ # --- Load API Key ---
+ load_dotenv()
+ 
++# Check if API key exists
++GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
++if not GOOGLE_API_KEY:
++    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
++
++# Set the API key for the SDK
++os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
++
+ # Initialize the Generative AI model
+ llm = ChatGoogleGenerativeAI(
+-    model="gemini-2.5-flash", 
++    model="gemini-2.5-flash-lite", 
+     temperature=0.2 
+ )
+ 
+@@ -22,59 +30,57 @@ def get_analyzer_chain():
+     """
+     
+     system_prompt = """
+-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
+-    and determine if the change is a 'trivial' change (like fixing a typo, 
+-    adding comments, or refactoring code) or a 'functional' change 
+-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+-
+-    You MUST respond in JSON format with two keys:
+-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+-
+-    Examples:
+-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+-    """
++You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
++and determine if the change is a 'trivial' change (like fixing a typo, 
++adding comments, or refactoring code) or a 'functional' change 
++(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
++
++You MUST respond in JSON format with two keys:
++1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
++2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
++   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
++
++Examples:
++- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
++- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
++- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
+ 
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        OLD DOCUMENTATION SNIPPETS:
+-        {old_docs_context}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please provide the new, updated documentation based on these changes:
+-        """)
++Here is the context:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++OLD DOCUMENTATION SNIPPETS:
++{old_docs_context}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please provide the new, updated documentation based on these changes:
+ """)
+     ])
+     
+     return analyzer_chain
+ 
+-# --- 2. The "Rewriter" Chain (UPDATED) ---
+-# --- 2. The "Rewriter" Chain ---
+ 
+ def get_rewriter_chain():
+     """
+     Returns a chain that rewrites documentation.
+     """
+     
+-    # --- THIS PROMPT IS UPDATED ---
+     system_prompt = """
+-    You are an expert technical writer. Your task is to rewrite old documentation 
+-    to match the new code changes.
++You are an expert technical writer. Your task is to rewrite old documentation 
++to match the new code changes.
+ 
+-    You will be given:
+-    1. The Old Documentation (as a list of relevant snippets).
+-    2. The 'git diff' of the new code.
+-    3. An analysis of what changed.
++You will be given:
++1. The Old Documentation (as a list of relevant snippets).
++2. The 'git diff' of the new code.
++3. An analysis of what changed.
+ 
+-    Your job is to return the new, rewritten documentation.
+-    - Maintain the original tone and formatting (e.g., Markdown).
+-    - Do not add commentary like "Here is the new documentation:".
+-    
+-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+-    the relevant code diff. The final output must be in this format:
+-    
+-    [Your rewritten documentation text]
+-    
+-    ---
+-    
+-    ### Relevant Code Changes
+-    ```diff
+-    [The exact 'git diff' you were provided]
+-    ```
+-    """
+-    # --- END OF UPDATE ---
++Your job is to return the new, rewritten documentation.
++- Maintain the original tone and formatting (e.g., Markdown).
++- Do not add commentary like "Here is the new documentation:".
++
++**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
++the relevant code diff. The final output must be in this format:
++
++[Your rewritten documentation text]
++
++---
++
++### Relevant Code Changes
++```diff
++[The exact 'git diff' you were provided]
++```
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        OLD DOCUMENTATION SNIPPETS:
+-        {old_docs_context}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please provide the new, updated documentation based on these changes:
+-        """)
++Here is the context:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++OLD DOCUMENTATION SNIPPETS:
++{old_docs_context}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please provide the new, updated documentation based on these changes:
+ """)
+     ])
+     
+     # We pipe this to the LLM and then to a simple string parser
+@@ -82,79 +88,79 @@ def get_rewriter_chain():
+     
+     return rewriter_chain
+ 
+-# --- 3. The "Creator" Chain (NEW) ---
++# --- 3. The "Creator" Chain ---
+ 
+ def get_creator_chain():
+     """
+     Returns a chain that creates a NEW documentation section from scratch
+     when no existing documentation is found.
+     """
+-    system_prompt = """
+-    You are an expert technical writer tasked with creating a new documentation
+-    section for a feature that has no prior documentation.
+-
+-    You will be given:
+-    1. A 'git diff' of the new code.
+-    2. An AI-generated analysis of what changed.
+-
+-    Your job is to write a clear, concise documentation section explaining the new
+-    feature. The output should be ready to be added to a larger document.
+-    - Use Markdown formatting.
+-    - Explain the feature's purpose and how it works based on the code.
+-    - Do not add commentary like "Here is the new documentation:".
+-    """
++    system_prompt = """You are an expert technical writer tasked with creating a new documentation
++section for a feature that has no prior documentation.
++
++You will be given:
++1. A 'git diff' of the new code.
++2. An AI-generated analysis of what changed.
++
++Your job is to write a clear, concise documentation section explaining the new
++feature. The output should be ready to be added to a larger document.
++- Use Markdown formatting.
++- Explain the feature's purpose and how it works based on the code.
++- Do not add commentary like "Here is the new documentation:".
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the context for the new feature:
+-        
+-        ANALYSIS OF CHANGE:
+-        {analysis_summary}
+-        
+-        CODE CHANGE (GIT DIFF):
+-        ```diff
+-        {git_diff}
+-        ```
+-        
+-        Please write a new documentation section for this feature:
+-        """)
++Here is the context for the new feature:
++
++ANALYSIS OF CHANGE:
++{analysis_summary}
++
++CODE CHANGE (GIT DIFF):
++```diff
++{git_diff}
++```
++
++Please write a new documentation section for this feature:
+ """)
+     ])
+     
+     creator_chain = prompt | llm | StrOutputParser()
+     return creator_chain
+ 
+-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
+-# --- 4. The "Summarizer" Chain ---
+ 
+ def get_summarizer_chain():
+     """
+     Returns a chain that creates a simple, human-readable summary of a change
+-    for logging purposes, in the format you requested.
++    for logging purposes.
+     """
+     system_prompt = """
+-    You are a technical project manager who writes concise, formal changelogs.
+-    Based on the provided analysis and git diff, produce a single sentence that
+-    describes the change and its impact.
++You are a technical project manager who writes concise, formal changelogs.
++Based on the provided analysis and git diff, produce a single sentence that
++describes the change and its impact.
+ 
+-    Your response MUST be a single sentence that follows the format:
+-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
++Your response MUST be a single sentence that follows the format:
++"A push by {user_name} to the file `<file_name>` has <impact_description>."
+ 
+-    - You must determine the most relevant `<file_name>` from the git diff.
+-    - You must write the `<impact_description>` based on the AI analysis.
+-    - Keep the `impact_description` brief and high-level.
+-    - Do not include "from this to that" or line numbers.
+-    """
++    - You must determine the most relevant `<file_name>` from the git diff.
++    - You must write the `<impact_description>` based on the AI analysis.
++    - Keep the `impact_description` brief and high-level.
++    - Do not include "from this to that" or line numbers.
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        CONTEXT:
+-        - User: {user_name}
+-        - AI Analysis: {analysis_summary}
+-        - Git Diff:
+-        ```diff
+-        {git_diff}
+-        ```
+-        Please provide the single-sentence summary for the changelog:
+-        """)
++CONTEXT:
++- User: {user_name}
++- AI Analysis: {analysis_summary}
++- Git Diff:
++```diff
++{git_diff}
++```
++Please provide the single-sentence summary for the changelog:
+ """)
+     ])
+     
+     summarizer_chain = prompt | llm | StrOutputParser()
+     return summarizer_chain
+ 
+-# --- 5. The "Seeder" Chain (NEW) ---
+-# --- 5. The "Seeder" Chain ---
+ 
+ def get_seeder_chain():
+     """
+@@ -162,31 +168,31 @@ def get_seeder_chain():
+     to seed the knowledge base.
+     """
+     system_prompt = """
+-    You are an expert technical writer tasked with creating a high-level project overview
+-    to serve as the initial knowledge base for a software project.
++You are an expert technical writer tasked with creating a high-level project overview
++to serve as the initial knowledge base for a software project.
+ 
+-    You will be given the concatenated source code of the project's key files.
++You will be given the concatenated source code of the project's key files.
+ 
+-    Your job is to write a "README" style document that explains:
+-    1.  What the project is and its main purpose.
+-    2.  The core technologies used.
+-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
++Your job is to write a "README" style document that explains:
++1. What the project is and its main purpose.
++2. The core technologies used.
++3. A brief explanation of how the main components work together.
+ 
+-    The output should be in Markdown format and serve as a good starting point for project documentation.
+-    Do not add commentary like "Here is the new documentation:".
+-    """
++The output should be in Markdown format and serve as a good starting point for project documentation.
++Do not add commentary like "Here is the new documentation:".
+ """
+     
+     prompt = ChatPromptTemplate.from_messages([
+         ("system", system_prompt),
+         ("human", """
+-        Here is the source code of the project:
+-        
+-        ```python
+-        {source_code}
+-        ```
+-        
+-        Please generate the initial project documentation based on this code.
+-        """)
++Here is the source code of the project:
++
++```python
++{source_code}
++```
++
++Please generate the initial project documentation based on this code.
+ """)
+     ])
+     
+     seeder_chain = prompt | llm | StrOutputParser()
+@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
+ # --- Self-Test ---
+ if __name__ == "__main__":
+     
+-    print("--- Running LLM Clients Self-Test ---")
++    print("=" * 70)
++    print("Running Complete Doc-Ops LLM Chains Self-Test")
++    print("=" * 70)
+     
+-    # Test data
+-    test_diff_functional = """
+-    --- a/api/routes.py
+++++ b/api/routes.py
++@@ -10,5 +10,6 @@
++ @app.route('/api/v1/users')
++ def get_users():
++     return jsonify(users)
+++
+++@app.route('/api/v1/users/profile')
+++def get_user_profile():
+++    return jsonify({"name": "Test User", "status": "active"})
++"""
+     
+-    # 1. Test Analyzer Chain
+-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
++    test_diff_trivial = """
++--- a/api/routes.py
+++++ b/api/routes.py
++@@ -1,3 +1,4 @@
++ # This file contains all API routes for our app.
++ from flask import Flask, jsonify
++
+++# TODO: Add more routes later
++"""
+     
+     # 1. Test Analyzer Chain (Functional Change)
+     print("\n" + "-" * 70)
+     print("Test 1: Analyzer Chain (Functional Change)")
+     print("-" * 70)
+     try:
+         analyzer = get_analyzer_chain()
+-        test_diff_functional = """
+-        --- a/api/routes.py
+-        +++ b/api/routes.py
+-        @@ -10,5 +10,6 @@
+-         @app.route('/api/v1/users')
+-         def get_users():
+-             return jsonify(users)
+-        +
+-        +@app.route('/api/v1/users/profile')
+-        +def get_user_profile():
+-        +    return jsonify({"name": "Test User", "status": "active"})
+-        """
+         analysis = analyzer.invoke({"git_diff": test_diff_functional})
+         print(f"Response:\n{analysis}")
+         assert analysis['is_functional_change'] == True
+-        print("Test Passed.")
++        print("✅ Test 1 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
+-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
++        print(f"❌ Test 1 Failed: {e}")
++        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+ 
+     # 2. Test Analyzer Chain (Trivial Change)
+-    print("\n--- Testing Analyzer Chain (Trivial Change) ---")
++    print("\n" + "-" * 70)
++    print("Test 2: Analyzer Chain (Trivial Change)")
++    print("-" * 70)
+     try:
+         analyzer = get_analyzer_chain()
+-        test_diff_trivial = """
+-        --- a/api/routes.py
+-        +++ b/api/routes.py
+-        @@ -1,3 +1,3 @@
+-         # This file contains all API routes for our app.
+-         from flask import Flask, jsonify
+-         
+-         # TODO: Add more routes later
+-        """
+         analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+         print(f"Response:\n{analysis}")
+         assert analysis['is_functional_change'] == False
+-        print("Test Passed.")
++        print("✅ Test 2 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
++        print(f"❌ Test 2 Failed: {e}")
+ 
+     # 3. Test Rewriter Chain
+-    print("\n--- Testing Rewriter Chain ---")
++    print("\n" + "-" * 70)
++    print("Test 3: Rewriter Chain")
++    print("-" * 70)
+     try:
+-        rewriter = get_rewriter_chain() # <-- Fixed typo
++        rewriter = get_rewriter_chain()
+         test_old_docs = [
+-            Document(page_content="Our API has one user endpoint: /api/v1/users.", metadata={"source": "api.md"})
++            Document(
++                page_content="Our API has one user endpoint: /api/v1/users.", 
++                metadata={"source": "api.md"}
++            )
+         ]
+         formatted_docs = format_docs_for_context(test_old_docs)
+         
+@@ -273,8 +293,76 @@ def get_users():
+         })
+         print(f"Response:\n{rewrite}")
+         assert "/api/v1/users/profile" in rewrite
+-        assert "Relevant Code Changes" in rewrite # Test new instruction
+-        assert "--- a/api/routes.py" in rewrite # Test if diff is included
+-        print("Test Passed.")
++        print("✅ Test 3 Passed!")
+     except Exception as e:
+-        print(f"Test Failed: {e}")
+\ No newline at end of file
+         print(f"❌ Test 3 Failed: {e}")
++
++    # 4. Test Creator Chain
++    print("\n" + "-" * 70)
++    print("Test 4: Creator Chain (New Documentation)")
++    print("-" * 70)
++    try:
++        creator = get_creator_chain()
++        new_docs = creator.invoke({
++            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
++            "git_diff": test_diff_functional
++        })
++        print(f"Response:\n{new_docs}")
++        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
++        print("✅ Test 4 Passed!")
+     except Exception as e:
++        print(f"❌ Test 4 Failed: {e}")
++
++    # 5. Test Summarizer Chain
++    print("\n" + "-" * 70)
++    print("Test 5: Summarizer Chain (Changelog)")
++    print("-" * 70)
++    try:
++        summarizer = get_summarizer_chain()
++        summary = summarizer.invoke({
++            "user_name": "john_doe",
++            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
++            "git_diff": test_diff_functional
++        })
++        print(f"Response:\n{summary}")
++        assert "john_doe" in summary or "api/routes.py" in summary
++        print("✅ Test 5 Passed!")
+     except Exception as e:
++        print(f"❌ Test 5 Failed: {e}")
++
++    # 6. Test Seeder Chain
++    print("\n" + "-" * 70)
++    print("Test 6: Seeder Chain (Initial Project Documentation)")
++    print("-" * 70)
++    try:
++        seeder = get_seeder_chain()
++        test_source_code = """
++from flask import Flask, jsonify
++
++app = Flask(__name__)
++
++@app.route('/api/v1/users')
++def get_users():
++    return jsonify({'users': ['Alice', 'Bob']})
++
++if __name__ == '__main__':
++    app.run(debug=True)
++"""
++        seed_docs = seeder.invoke({"source_code": test_source_code})
++        print(f"Response:\n{seed_docs}")
++        assert "Flask" in seed_docs or "API" in seed_docs
++        print("✅ Test 6 Passed!")
+     except Exception as e:
++        print(f"❌ Test 6 Failed: {e}")
++    
+     # Final Summary
+     print("\n" + "=" * 70)
+     print("Self-Test Complete!")
+     print("=" * 70)
+     print("\n💡 All chains are ready to use:")
+     print("   1. Analyzer Chain - Detects functional vs trivial changes")
+     print("   2. Rewriter Chain - Updates existing documentation")
+     print("   3. Creator Chain - Creates new documentation from scratch")
+     print("   4. Summarizer Chain - Generates changelog summaries")
+     print("   5. Seeder Chain - Creates initial project documentation")
+     print("=" * 70)
+\ No newline at end of file
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+\ No newline at end of file
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+```
diff --git a/backend/doc_ops_agent.log b/backend/doc_ops_agent.log
index 1679431..73b3ae7 100644
--- a/backend/doc_ops_agent.log
+++ b/backend/doc_ops_agent.log
@@ -1884,3 +1884,7 @@ Please retry in 19.003457153s. [links {
 2025-11-16 14:35:13,923 - Successfully updated file: backend/llm_clients.py
 2025-11-16 14:35:15,985 - This is an AI-generated documentation update for PR #a83ade0, originally authored by @livingcool.
 Original PR: 'Push to main: updated the logic' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
+2025-11-16 15:56:55,691 - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
+2025-11-16 15:57:11,092 - Successfully updated file: backend/data/Knowledge_Base.md
+2025-11-16 15:57:13,153 - This is an AI-generated documentation update for PR #7fc6e13, originally authored by @livingcool.
+Original PR: 'Push to main: Change the name of the application' AI Analysis: Functional change: Introduced a 'Create Mode' for documentation generation, allowing the system to create new documentation entries when relevant existing docs are not found or confidence is low, rather than just updating or skipping.
diff --git a/backend/faiss_index/index.faiss b/backend/faiss_index/index.faiss
index f15e01d..df4820a 100644
Binary files a/backend/faiss_index/index.faiss and b/backend/faiss_index/index.faiss differ
diff --git a/backend/faiss_index/index.pkl b/backend/faiss_index/index.pkl
index 660ada7..bd0b01d 100644
Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
index df28c5f..b4018b5 100644
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -11,7 +11,8 @@ import { LogIcon } from './components/LogIcon.jsx';
 
 import './App.css'; // Your component styles
 
-const BACKEND_STREAM_URL = "http://localhost:8000/api/stream/logs";
+const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
+const BACKEND_STREAM_URL = `${BACKEND_URL}/api/stream/logs`;
 
 export default function App() {
   const { logs, status } = useEventSource(BACKEND_STREAM_URL);
@@ -27,7 +28,7 @@ export default function App() {
         <LogIcon type="log-error" />
         <div className="log-message">
-          Could not connect to backend at <code>{BACKEND_STREAM_URL}</code>.
+          Could not connect to backend at <code>{BACKEND_URL}</code>.
           Is the FastAPI server running on port 8000?
         </div>
       </motion.div>
```


---

### AI-Generated Update (2025-11-16 17:40:10)

# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store.
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
*   **Git**: [Download Git](https://git-scm.com/downloads/)
*   **GitHub Account**: You will need a personal GitHub account.
*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/livingcool/doc-ops-agent.git
    cd doc-ops-agent
    ```

2.  **Set up Backend Environment**:
    *   Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
        ```dotenv
        # .env file in backend/ directory
        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
        ```

3.  **Set up Frontend Environment**:
    *   Navigate to the `frontend/` directory:
        ```bash
        cd frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

4.  **Initialize the Vector Store**:
    *   Run the Python script to load initial documentation (if any) into the FAISS index:
        ```bash
        python ../backend/vector_store.py
        ```
        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.

## 5. Configuration

### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "DocSmith").
4.  Set the **Expiration** as needed (e.g., 90 days).
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
    *   `admin:repo_hook` (Full control of repository hooks)
6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.

### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.

### 5.3 Google AI API Key (`GOOGLE_API_KEY`)

1.  Log in to your Google AI Studio account.
2.  Go to the **API Key** section.
3.  Create a new API key or use an existing one.
4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.

### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)

This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.

## 6. Running the Application

1.  **Start the Backend Server**:
    *   Activate your backend virtual environment (`source venv/bin/activate`).
    *   Run the FastAPI application:
        ```bash
        cd backend
        uvicorn main:app --reload --port 8000
        ```

2.  **Start the Frontend Development Server**:
    *   Open a new terminal.
    *   Navigate to the `frontend/` directory.
    *   Run the React development server:
        ```bash
        cd frontend
        npm start
        ```
    *   The frontend will be available at `http://localhost:3000`.

3.  **Expose your Local Server with ngrok**:
    *   Open another terminal.
    *   Run ngrok to expose your local backend server to the internet:
        ```bash
        ngrok http 8000
        ```
    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).

4.  **Configure GitHub Webhook**:
    *   Go to your GitHub repository's **Settings** > **Webhooks**.
    *   Click **Add webhook**.
    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
    *   **Content type**: Select `application/json`.
    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
    *   Ensure **Active** is checked.
    *   Click **Add webhook**.

## 7. How to Use DocSmith

Your setup is complete! Now you can test DocSmith's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

---

You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.

## 8. Deployment to Render

To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.

1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
2.  **Configure the service** with the following settings:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

## 9. Deployment (Frontend to Vercel)

To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.

1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
3.  **Configure Project**:
    *   Vercel will automatically detect that it's a Create React App.
    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
4.  **Configure Environment Variables**:
    *   This is the most important step. Expand the "Environment Variables" section.
    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.

---

You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!

---

### AI-Generated Update (2025-11-16 17:31:28)

# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store.
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
*   **Git**: [Download Git](https://git-scm.com/downloads/)
*   **GitHub Account**: You will need a personal GitHub account.
*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/livingcool/doc-ops-agent.git
    cd doc-ops-agent
    ```

2.  **Set up Backend Environment**:
    *   Create a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
        ```dotenv
        # .env file in backend/ directory
        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
        ```

3.  **Set up Frontend Environment**:
    *   Navigate to the `frontend/` directory:
        ```bash
        cd frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

4.  **Initialize the Vector Store**:
    *   Run the Python script to load initial documentation (if any) into the FAISS index:
        ```bash
        python ../backend/vector_store.py
        ```
        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.

## 5. Configuration

### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "DocSmith").
4.  Set the **Expiration** as needed (e.g., 90 days).
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
    *   `admin:repo_hook` (Full control of repository hooks)
6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.

### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.

### 5.3 Google AI API Key (`GOOGLE_API_KEY`)

1.  Log in to your Google AI Studio account.
2.  Go to the **API Key** section.
3.  Create a new API key or use an existing one.
4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.

### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)

This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.

## 6. Running the Application

1.  **Start the Backend Server**:
    *   Activate your backend virtual environment (`source venv/bin/activate`).
    *   Run the FastAPI application:
        ```bash
        cd backend
        uvicorn main:app --reload --port 8000
        ```

2.  **Start the Frontend Development Server**:
    *   Open a new terminal.
    *   Navigate to the `frontend/` directory.
    *   Run the React development server:
        ```bash
        cd frontend
        npm start
        ```
    *   The frontend will be available at `http://localhost:3000`.

3.  **Expose your Local Server with ngrok**:
    *   Open another terminal.
    *   Run ngrok to expose your local backend server to the internet:
        ```bash
        ngrok http 8000
        ```
    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).

4.  **Configure GitHub Webhook**:
    *   Go to your GitHub repository's **Settings** > **Webhooks**.
    *   Click **Add webhook**.
    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
    *   **Content type**: Select `application/json`.
    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
    *   Ensure **Active** is checked.
    *   Click **Add webhook**.

## 7. How to Use DocSmith

Your setup is complete! Now you can test DocSmith's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

---

You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.

## 8. Deployment to Render

To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.

1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
2.  **Configure the service** with the following settings:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
        *   Use the port recommended by Render (e.g., `10000`).
3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).

Your agent is now live and will run automatically in the cloud!

---

### AI-Generated Update (2025-11-16 14:34:57)

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
index 7453050..125ae6b 100644
--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
     with open(file_path, "a", encoding="utf-8") as f:
         f.write(content)
 
++++def _extract_changed_lines(git_diff: str) -> str:
++++    """A helper to extract only the added/modified lines from a git diff."""
++++    changed_lines = []
++++    for line in git_diff.split('\n'):
++++        # We only care about lines that were added.
++++        if line.startswith('+') and not line.startswith('+++'):
++++            changed_lines.append(line[1:]) # Remove the '+'
++++    
++++    return "\n".join(changed_lines)
++++
 + # --- Updated Core Agent Logic ---
 + 
 + async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
++++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++++        concise_diff = _extract_changed_lines(git_diff)
++++        if not concise_diff:
++++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++++            return
++++
 +         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
 -        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
 
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff # Use the concise diff here as well
         })
         # Broadcast the clean summary instead of the raw analysis
         await broadcaster("log-summary", human_readable_summary)
@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
             new_documentation = await creator_chain.ainvoke({
                 "analysis_summary": analysis_summary,
-                "git_diff": git_diff
+                "git_diff": concise_diff # Use the concise diff
             })
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
             if confidence_score > 0:
@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             new_documentation = await rewriter_chain.ainvoke({
                 "analysis_summary": analysis_summary,
                 "old_docs_context": old_docs_context,
-                "git_diff": git_diff
+                "git_diff": git_diff # The rewriter gets the full diff for context
             })
             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
 
@@ -222,8 +238,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
+        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
++++ b/backend/llm_clients.py
@@ -8,9 +8,17 @@
 # --- Load API Key ---
 load_dotenv()
 
+# Check if API key exists
+GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
+if not GOOGLE_API_KEY:
+    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
+
+# Set the API key for the SDK
+os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
+
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-2.5-flash", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
@@ -22,59 +30,57 @@ def get_analyzer_chain():
     """
     
     system_prompt = """
-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
-    and determine if the change is a 'trivial' change (like fixing a typo, 
-    adding comments, or refactoring code) or a 'functional' change 
-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
-
-    You MUST respond in JSON format with two keys:
-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
-
-    Examples:
-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
-    """
+You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
+and determine if the change is a 'trivial' change (like fixing a typo, 
+adding comments, or refactoring code) or a 'functional' change 
+(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+
+You MUST respond in JSON format with two keys:
+1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+
+Examples:
+- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     return analyzer_chain
 
-# --- 2. The "Rewriter" Chain (UPDATED) ---
-# --- 2. The "Rewriter" Chain ---
+# --- 2. The "Rewriter" Chain ---
 
 def get_rewriter_chain():
     """
     Returns a chain that rewrites documentation.
     """
     
-    # --- THIS PROMPT IS UPDATED ---
     system_prompt = """
-    You are an expert technical writer. Your task is to rewrite old documentation 
-    to match the new code changes.
+You are an expert technical writer. Your task is to rewrite old documentation 
+to match the new code changes.
 
-    You will be given:
-    1. The Old Documentation (as a list of relevant snippets).
-    2. The 'git diff' of the new code.
-    3. An analysis of what changed.
+You will be given:
+1. The Old Documentation (as a list of relevant snippets).
+2. The 'git diff' of the new code.
+3. An analysis of what changed.
 
-    Your job is to return the new, rewritten documentation.
-    - Maintain the original tone and formatting (e.g., Markdown).
-    - Do not add commentary like "Here is the new documentation:".
-    
-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
-    the relevant code diff. The final output must be in this format:
-    
-    [Your rewritten documentation text]
-    
-    ---
-    
-    ### Relevant Code Changes
-    ```diff
-    [The exact 'git diff' you were provided]
-    ```
-    """
-    # --- END OF UPDATE ---
+Your job is to return the new, rewritten documentation.
+- Maintain the original tone and formatting (e.g., Markdown).
+- Do not add commentary like "Here is the new documentation:".
+
+**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+the relevant code diff. The final output must be in this format:
+
+[Your rewritten documentation text]
+
+---
+
+### Relevant Code Changes
+```diff
+[The exact 'git diff' you were provided]
+```
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     # We pipe this to the LLM and then to a simple string parser
@@ -82,79 +88,79 @@ def get_rewriter_chain():
     
     return rewriter_chain
 
-# --- 3. The "Creator" Chain (NEW) ---
-# --- 3. The "Creator" Chain ---
+# --- 3. The "Creator" Chain ---
 
 def get_creator_chain():
     """
     Returns a chain that creates a NEW documentation section from scratch
     when no existing documentation is found.
     """
-    system_prompt = """
-    You are an expert technical writer tasked with creating a new documentation
-    section for a feature that has no prior documentation.
-
-    You will be given:
-    1. A 'git diff' of the new code.
-    2. An AI-generated analysis of what changed.
-
-    Your job is to write a clear, concise documentation section explaining the new
-    feature. The output should be ready to be added to a larger document.
-    - Use Markdown formatting.
-    - Explain the feature's purpose and how it works based on the code.
-    - Do not add commentary like "Here is the new documentation:".
-    """
+    system_prompt = """You are an expert technical writer tasked with creating a new documentation
+section for a feature that has no prior documentation.
+
+You will be given:
+1. A 'git diff' of the new code.
+2. An AI-generated analysis of what changed.
+
+Your job is to write a clear, concise documentation section explaining the new
+feature. The output should be ready to be added to a larger document.
+- Use Markdown formatting.
+- Explain the feature's purpose and how it works based on the code.
+- Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context for the new feature:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please write a new documentation section for this feature:
-        """)
+Here is the context for the new feature:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please write a new documentation section for this feature:
+ """)
     ])
     
     creator_chain = prompt | llm | StrOutputParser()
     return creator_chain
 
-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
-# --- 4. The "Summarizer" Chain ---
+# --- 4. The "Summarizer" Chain ---
 
 def get_summarizer_chain():
     """
     Returns a chain that creates a simple, human-readable summary of a change
-    for logging purposes, in the format you requested.
+    for logging purposes.
     """
     system_prompt = """
-    You are a technical project manager who writes concise, formal changelogs.
-    Based on the provided analysis and git diff, produce a single sentence that
-    describes the change and its impact.
+You are a technical project manager who writes concise, formal changelogs.
+Based on the provided analysis and git diff, produce a single sentence that
+describes the change and its impact.
 
-    Your response MUST be a single sentence that follows the format:
-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
+Your response MUST be a single sentence that follows the format:
+"A push by {user_name} to the file `<file_name>` has <impact_description>."
 
-    - You must determine the most relevant `<file_name>` from the git diff.
-    - You must write the `<impact_description>` based on the AI analysis.
-    - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that" or line numbers.
-    """
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
+    - Keep the `impact_description` brief and high-level.
+    - Do not include "from this to that" or line numbers.
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        CONTEXT:
-        - User: {user_name}
-        - AI Analysis: {analysis_summary}
-        - Git Diff:
-        ```diff
-        {git_diff}
-        ```
-        Please provide the single-sentence summary for the changelog:
-        """)
+CONTEXT:
+- User: {user_name}
+- AI Analysis: {analysis_summary}
+- Git Diff:
+```diff
+{git_diff}
+```
+Please provide the single-sentence summary for the changelog:
+ """)
     ])
     
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 5. The "Seeder" Chain (NEW) ---
-# --- 5. The "Seeder" Chain ---
+# --- 5. The "Seeder" Chain ---
 
 def get_seeder_chain():
     """
@@ -162,31 +168,31 @@ def get_seeder_chain():
     to seed the knowledge base.
     """
     system_prompt = """
-    You are an expert technical writer tasked with creating a high-level project overview
-    to serve as the initial knowledge base for a software project.
+You are an expert technical writer tasked with creating a high-level project overview
+to serve as the initial knowledge base for a software project.
 
-    You will be given the concatenated source code of the project's key files.
+You will be given the concatenated source code of the project's key files.
 
-    Your job is to write a "README" style document that explains:
-    1.  What the project is and its main purpose.
-    2.  The core technologies used.
-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
+Your job is to write a "README" style document that explains:
+1. What the project is and its main purpose.
+2. The core technologies used.
+3. A brief explanation of how the main components work together.
 
-    The output should be in Markdown format and serve as a good starting point for project documentation.
-    Do not add commentary like "Here is the new documentation:".
-    """
+The output should be in Markdown format and serve as a good starting point for project documentation.
+Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the source code of the project:
-        
-        ```python
-        {source_code}
-        ```
-        
-        Please generate the initial project documentation based on this code.
-        """)
+Here is the source code of the project:
+
+```python
+{source_code}
+```
+
+Please generate the initial project documentation based on this code.
+ """)
     ])
     
     seeder_chain = prompt | llm | StrOutputParser()
@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
 # --- Self-Test ---
 if __name__ == "__main__":
     
-    print("--- Running LLM Clients Self-Test ---")
+    print("=" * 70)
+    print("Running Complete Doc-Ops LLM Chains Self-Test")
+    print("=" * 70)
     
-    # Test data
-    test_diff_functional = """
-    --- a/api/routes.py
-    +++ b/api/routes.py
-    @@ -10,5 +10,6 @@
-     @app.route('/api/v1/users')
-     def get_users():
-         return jsonify(users)
-    +
-    +@app.route('/api/v1/users/profile')
-    +def get_user_profile():
-    +    return jsonify({"name": "Test User", "status": "active"})
-    """
-     
-    # 1. Test Analyzer Chain
-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
+    # Test diffs
+    test_diff_functional = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -10,5 +10,6 @@
+ @app.route('/api/v1/users')
+ def get_users():
+     return jsonify(users)
++
++@app.route('/api/v1/users/profile')
++def get_user_profile():
++    return jsonify({"name": "Test User", "status": "active"})
+"""
+
+    test_diff_trivial = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -1,3 +1,4 @@
+ # This file contains all API routes for our app.
+ from flask import Flask, jsonify
+
++# TODO: Add more routes later
+"""
+
+    # 1. Test Analyzer Chain (Functional Change)
+    print("\n" + "-" * 70)
+    print("Test 1: Analyzer Chain (Functional Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_functional = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -10,5 +10,6 @@
-         @app.route('/api/v1/users')
-         def get_users():
-             return jsonify(users)
-        +
-        +@app.route('/api/v1/users/profile')
-        +def get_user_profile():
-        +    return jsonify({"name": "Test User", "status": "active"})
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_functional})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == True
-        print("Test Passed.")
+        print("✅ Test 1 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
+        print(f"❌ Test 1 Failed: {e}")
+        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+
+    # 2. Test Analyzer Chain (Trivial Change)
+    print("\n" + "-" * 70)
+    print("Test 2: Analyzer Chain (Trivial Change)")
+    print("-" * 70)
+    try:
+        analyzer = get_analyzer_chain()
+        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+        print(f"Response:\n{analysis}")
+        assert analysis['is_functional_change'] == False
+        print("✅ Test 2 Passed!")
+    except Exception as e:
+        print(f"❌ Test 2 Failed: {e}")
+
+    # 3. Test Rewriter Chain
+    print("\n" + "-" * 70)
+    print("Test 3: Rewriter Chain")
+    print("-" * 70)
+    try:
+        rewriter = get_rewriter_chain()
+        test_old_docs = [
+            Document(
+                page_content="Our API has one user endpoint: /api/v1/users.", 
+                metadata={"source": "api.md"}
+            )
+        ]
+        formatted_docs = format_docs_for_context(test_old_docs)
+        
+        rewrite = rewriter.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "old_docs_context": formatted_docs,
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{rewrite}")
+        assert "/api/v1/users/profile" in rewrite
+        print("✅ Test 3 Passed!")
+    except Exception as e:
+        print(f"❌ Test 3 Failed: {e}")
+
+    # 4. Test Creator Chain
+    print("\n" + "-" * 70)
+    print("Test 4: Creator Chain (New Documentation)")
+    print("-" * 70)
+    try:
+        creator = get_creator_chain()
+        new_docs = creator.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{new_docs}")
+        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
+        print("✅ Test 4 Passed!")
+    except Exception as e:
+        print(f"❌ Test 4 Failed: {e}")
+
+    # 5. Test Summarizer Chain
+    print("\n" + "-" * 70)
+    print("Test 5: Summarizer Chain (Changelog)")
+    print("-" * 70)
+    try:
+        summarizer = get_summarizer_chain()
+        summary = summarizer.invoke({
+            "user_name": "john_doe",
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{summary}")
+        assert "john_doe" in summary or "api/routes.py" in summary
+        print("✅ Test 5 Passed!")
+    except Exception as e:
+        print(f"❌ Test 5 Failed: {e}")
+
+    # 6. Test Seeder Chain
+    print("\n" + "-" * 70)
+    print("Test 6: Seeder Chain (Initial Project Documentation)")
+    print("-" * 70)
+    try:
+        seeder = get_seeder_chain()
+        test_source_code = """
+from flask import Flask, jsonify
+
+app = Flask(__name__)
+
+@app.route('/api/v1/users')
+def get_users():
+    return jsonify({'users': ['Alice', 'Bob']})
+
+if __name__ == '__main__':
+    app.run(debug=True)
+"""
+        seed_docs = seeder.invoke({"source_code": test_source_code})
+        print(f"Response:\n{seed_docs}")
+        assert "Flask" in seed_docs or "API" in seed_docs
+        print("✅ Test 6 Passed!")
+    except Exception as e:
+        print(f"❌ Test 6 Failed: {e}")
+    
+    # Final Summary
+    print("\n" + "=" * 70)
+    print("Self-Test Complete!")
+    print("=" * 70)
+    print("\n💡 All chains are ready to use:")
+    print("   1. Analyzer Chain - Detects functional vs trivial changes")
+    print("   2. Rewriter Chain - Updates existing documentation")
+    print("   3. Creator Chain - Creates new documentation from scratch")
+    print("   4. Summarizer Chain - Generates changelog summaries")
+    print("   5. Seeder Chain - Creates initial project documentation")
+    print("=" * 70)
+
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
+++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
+++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
+++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
+++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
+++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
+index 629049c..6fc069a 100644
+--- a/backend/USER_GUIDE.md
++++ b/backend/USER_GUIDE.md
+@@ -1,10 +1,10 @@
+-# Doc-Ops Agent: User & Setup Guide
++# DocSmith: User & Setup Guide
+ 
+-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+ 
+ ## 1. Overview
+ 
+-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+ 
+ 1.  **Analyzes the code diff** using an AI model (OpenAI).
+ 2.  **Determines if the change is significant** enough to warrant a documentation update.
+@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
+ 
+ ## 2. Core Technologies
+ 
+-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
+ *   **Frontend**: React, Server-Sent Events (SSE) for live logging
+ *   **Vector Store**: FAISS for efficient similarity search
+ 
+@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
+ -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
+ -   **Git**: [Download Git](https://git-scm.com/downloads/)
+ -   **GitHub Account**: You will need a personal GitHub account.
+-*   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
+ -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
+ 
+ ## 4. Setup and Installation
+@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
+     # Your GitHub Personal Access Token for API actions
+     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
+ 
+-    # Your OpenAI API key
+-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
++    # Your Google AI API key for Gemini
++    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
+ 
+     # (Optional) The minimum confidence score required to update a document
+     CONFIDENCE_THRESHOLD=0.2
+@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
+ 2.  Click **Generate new token** (or **Generate new token (classic)**).
+-*   Give it a descriptive name (e.g., "Doc-Ops Agent").
++*   Give it a descriptive name (e.g., "DocSmith").
+  4.  Set the **Expiration** as needed (e.g., 90 days).
+  5.  Select the following **scopes**:
+      *   `repo` (Full control of private repositories)
+@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
+ 
+-#### OpenAI API Key (`OPENAI_API_KEY`)
++#### Google AI API Key (`GOOGLE_API_KEY`)
+ 
+ 1.  Log in to your OpenAI Platform account.
+ 2.  Go to the **API Keys** section.
+@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
+ 
+ ## 8. How to Use the Agent
+ 
+-Your setup is complete! Now you can test the agent's workflow.
++Your setup is complete! Now you can test DocSmith's workflow.
+ 
+ 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
+ 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
+ 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
+ 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
+-*   **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
++*   **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
+  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
+ 
+  ---
+ 
+-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+ 
+ ## 9. Deployment to Render
+ 
+-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
+ 
+  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
+  2.  **Configure the service** with the following settings:
+@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
+          *   Use the port recommended by Render (e.g., `10000`).
+   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
+-*   **Deploy**: Trigger a manual deploy.
++*   **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+  Your agent is now live and will run automatically in the cloud!
+@@ -211,4 +211,23 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+  4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+-Your agent is now live and will run automatically in the cloud!
+\ No newline at end of file
++Your agent is now live and will run automatically in the cloud!
++
++## 10. Deployment (Frontend to Vercel)
++
++To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.
++
++1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
++2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
++3.  **Configure Project**:
++    *   Vercel will automatically detect that it's a Create React App.
++    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
++4.  **Configure Environment Variables**:
++    *   This is the most important step. Expand the "Environment Variables" section.
++    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
++    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
++5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.
++
++---
++
++You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!
+\ No newline at end of file
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 28f6635..0e5420a 100644
+--- a/backend/data/@Knowledge_base.md
++++ b/backend/data/@Knowledge_base.md
+@@ -1122,3 +1122,1393 @@ index f422459..4556d9d 100644
+ Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
+ 
+ ```
++
++
++---
++
++### AI-Generated Update (2025-11-16 15:56:55)
++
++# DocSmith: User & Setup Guide
++
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++
++## 1. Overview
++
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++
++1.  **Analyzes the code diff** using an AI model (Google Gemini).
++2.  **Determines if the change is significant** enough to warrant a documentation update.
++3.  **Retrieves relevant existing documentation** snippets from a vector store.
++4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
++5.  **Creates a new pull request** with the documentation changes.
++
++## 2. Core Technologies
++
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
++*   **Frontend**: React, Server-Sent Events (SSE) for live logging
++*   **Vector Store**: FAISS for efficient similarity search
++
++## 3. Prerequisites
++
++Before you begin, ensure you have the following installed and configured:
++
++*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
++*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
++*   **Git**: [Download Git](https://git-scm.com/downloads/)
++*   **GitHub Account**: You will need a personal GitHub account.
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
++*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
++
++## 4. Setup and Installation
++
++1.  **Clone the Repository**:
++    ```bash
++    git clone https://github.com/livingcool/doc-ops-agent.git
++    cd doc-ops-agent
++    ```
++
++2.  **Set up Backend Environment**:
++    *   Create a virtual environment:
++        ```bash
++        python -m venv venv
++        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
++        ```
++    *   Install Python dependencies:
++        ```bash
++        pip install -r requirements.txt
++        ```
++    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
++        ```dotenv
++        # .env file in backend/ directory
++        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
++        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
++        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
++        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
++        ```
++
++3.  **Set up Frontend Environment**:
++    *   Navigate to the `frontend/` directory:
++        ```bash
++        cd frontend
++        ```
++    *   Install Node.js dependencies:
++        ```bash
++        npm install
++        ```
++
++4.  **Initialize the Vector Store**:
++    *   Run the Python script to load initial documentation (if any) into the FAISS index:
++        ```bash
++        python ../backend/vector_store.py
++        ```
++        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.
++
++## 5. Configuration
++
++### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)
++
++The agent needs this token to create branches and pull requests on your behalf.
++
++1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
++2.  Click **Generate new token** (or **Generate new token (classic)**).
++3.  Give it a descriptive name (e.g., "DocSmith").
++4.  Set the **Expiration** as needed (e.g., 90 days).
++5.  Select the following **scopes**:
++    *   `repo` (Full control of private repositories)
++    *   `admin:repo_hook` (Full control of repository hooks)
++6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.
++
++### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)
++
++This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.
++
++### 5.3 Google AI API Key (`GOOGLE_API_KEY`)
++
++1.  Log in to your Google AI Studio account.
++2.  Go to the **API Key** section.
++3.  Create a new API key or use an existing one.
++4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.
++
++### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)
++
++This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.
++
++## 6. Running the Application
++
++1.  **Start the Backend Server**:
++    *   Activate your backend virtual environment (`source venv/bin/activate`).
++    *   Run the FastAPI application:
++        ```bash
++        cd backend
++        uvicorn main:app --reload --port 8000
++        ```
++
++2.  **Start the Frontend Development Server**:
++    *   Open a new terminal.
++    *   Navigate to the `frontend/` directory.
++    *   Run the React development server:
++        ```bash
++        cd frontend
++        npm start
++        ```
++    *   The frontend will be available at `http://localhost:3000`.
++
++3.  **Expose your Local Server with ngrok**:
++    *   Open another terminal.
++    *   Run ngrok to expose your local backend server to the internet:
++        ```bash
++        ngrok http 8000
++        ```
++    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).
++
++4.  **Configure GitHub Webhook**:
++    *   Go to your GitHub repository's **Settings** > **Webhooks**.
++    *   Click **Add webhook**.
++    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
++    *   **Content type**: Select `application/json`.
++    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
++    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
++    *   Ensure **Active** is checked.
++    *   Click **Add webhook**.
++
++## 7. How to Use DocSmith
++
++Your setup is complete! Now you can test DocSmith's workflow.
++
++1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
++2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
++3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
++4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
++5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
++6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
++
++---
++
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++
++## 8. Deployment to Render
++
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
++
++1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
++2.  **Configure the service** with the following settings:
++    *   **Build Command**: `pip install -r requirements.txt`
++    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
++        *   Use the port recommended by Render (e.g., `10000`).
++3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
++4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
++5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
++
++Your agent is now live and will run automatically in the cloud!
++
++---
++
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
++++def _extract_changed_lines(git_diff: str) -> str:
++++    """A helper to extract only the added/modified lines from a git diff."""
++++    changed_lines = []
++++    for line in git_diff.split('\n'):
++++        # We only care about lines that were added.
++++        if line.startswith('+') and not line.startswith('+++'):
++++            changed_lines.append(line[1:]) # Remove the '+'
++++    
++++    return "\n".join(changed_lines)
++++
 + # --- Updated Core Agent Logic ---
 + 
 + async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
++++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++++        concise_diff = _extract_changed_lines(git_diff)
++++        if not concise_diff:
++++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++++            return
++++
 +         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
 -        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
 
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff # Use the concise diff here as well
         })
         # Broadcast the clean summary instead of the raw analysis
         await broadcaster("log-summary", human_readable_summary)
@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
             new_documentation = await creator_chain.ainvoke({
                 "analysis_summary": analysis_summary,
-                "git_diff": git_diff
+                "git_diff": concise_diff # Use the concise diff
             })
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
             if confidence_score > 0:
@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             new_documentation = await rewriter_chain.ainvoke({
                 "analysis_summary": analysis_summary,
                 "old_docs_context": old_docs_context,
-                "git_diff": git_diff
+                "git_diff": git_diff # The rewriter gets the full diff for context
             })
             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
 
@@ -222,8 +238,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
+        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index 4fb803e..dcfa93c 100644
--- a/backend/data/@Knowledge_base.md
++++++ b/backend/data/@Knowledge_base.md
@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
  def get_seeder_chain():
      """
  ```
++++
++++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
++++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
++++++    get_summarizer_chain,
++++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
++++++    creator_chain = get_creator_chain()
++++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
++++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
++++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
++++++            analysis_summary, k=5
++++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
++++++        retrieved_docs = [doc for doc, score in docs_with_scores]
++++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
++++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
++++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
++++++        pr_body_note = ""
++++++
++++++        if not retrieved_docs or confidence_score < confidence_threshold:
++++++            # CREATE MODE: No relevant docs found or confidence is too low.
++++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
++++++            new_documentation = await creator_chain.ainvoke({
++++++                "analysis_summary": analysis_summary,
++++++                "git_diff": git_diff
++++++            })
++++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
++++++            if confidence_score > 0:
++++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
 +         else:
 +             # UPDATE MODE: High confidence, proceed with rewriting.
 +             await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
@@ -212,8 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
++++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
++++ b/backend/llm_clients.py
@@ -8,9 +8,17 @@
 # --- Load API Key ---
 load_dotenv()
 
+# Check if API key exists
+GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
+if not GOOGLE_API_KEY:
+    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
+
+# Set the API key for the SDK
+os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
+
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-2.5-flash", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
@@ -22,59 +30,57 @@ def get_analyzer_chain():
     """
     
     system_prompt = """
-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
-    and determine if the change is a 'trivial' change (like fixing a typo, 
-    adding comments, or refactoring code) or a 'functional' change 
-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
-
-    You MUST respond in JSON format with two keys:
-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
-
-    Examples:
-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
-    """
+You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
+and determine if the change is a 'trivial' change (like fixing a typo, 
+adding comments, or refactoring code) or a 'functional' change 
+(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+
+You MUST respond in JSON format with two keys:
+1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+
+Examples:
+- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     return analyzer_chain
 
-# --- 2. The "Rewriter" Chain (UPDATED) ---
-# --- 2. The "Rewriter" Chain ---
+# --- 2. The "Rewriter" Chain ---
 
 def get_rewriter_chain():
     """
     Returns a chain that rewrites documentation.
     """
     
-    # --- THIS PROMPT IS UPDATED ---
     system_prompt = """
-    You are an expert technical writer. Your task is to rewrite old documentation 
-    to match the new code changes.
+You are an expert technical writer. Your task is to rewrite old documentation 
+to match the new code changes.
 
-    You will be given:
-    1. The Old Documentation (as a list of relevant snippets).
-    2. The 'git diff' of the new code.
-    3. An analysis of what changed.
+You will be given:
+1. The Old Documentation (as a list of relevant snippets).
+2. The 'git diff' of the new code.
+3. An analysis of what changed.
 
-    Your job is to return the new, rewritten documentation.
-    - Maintain the original tone and formatting (e.g., Markdown).
-    - Do not add commentary like "Here is the new documentation:".
-    
-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
-    the relevant code diff. The final output must be in this format:
-    
-    [Your rewritten documentation text]
-    
-    ---
-    
-    ### Relevant Code Changes
-    ```diff
-    [The exact 'git diff' you were provided]
-    ```
-    """
-    # --- END OF UPDATE ---
+Your job is to return the new, rewritten documentation.
+- Maintain the original tone and formatting (e.g., Markdown).
+- Do not add commentary like "Here is the new documentation:".
+
+**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+the relevant code diff. The final output must be in this format:
+
+[Your rewritten documentation text]
+
+---
+
+### Relevant Code Changes
+```diff
+[The exact 'git diff' you were provided]
+```
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     # We pipe this to the LLM and then to a simple string parser
@@ -82,79 +88,79 @@ def get_rewriter_chain():
     
     return rewriter_chain
 
-# --- 3. The "Creator" Chain (NEW) ---
-# --- 3. The "Creator" Chain ---
+# --- 3. The "Creator" Chain ---
 
 def get_creator_chain():
     """
     Returns a chain that creates a NEW documentation section from scratch
     when no existing documentation is found.
     """
-    system_prompt = """
-    You are an expert technical writer tasked with creating a new documentation
-    section for a feature that has no prior documentation.
-
-    You will be given:
-    1. A 'git diff' of the new code.
-    2. An AI-generated analysis of what changed.
-
-    Your job is to write a clear, concise documentation section explaining the new
-    feature. The output should be ready to be added to a larger document.
-    - Use Markdown formatting.
-    - Explain the feature's purpose and how it works based on the code.
-    - Do not add commentary like "Here is the new documentation:".
-    """
+    system_prompt = """You are an expert technical writer tasked with creating a new documentation
+section for a feature that has no prior documentation.
+
+You will be given:
+1. A 'git diff' of the new code.
+2. An AI-generated analysis of what changed.
+
+Your job is to write a clear, concise documentation section explaining the new
+feature. The output should be ready to be added to a larger document.
+- Use Markdown formatting.
+- Explain the feature's purpose and how it works based on the code.
+- Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context for the new feature:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please write a new documentation section for this feature:
-        """)
+Here is the context for the new feature:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please write a new documentation section for this feature:
+ """)
     ])
     
     creator_chain = prompt | llm | StrOutputParser()
     return creator_chain
 
-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
-# --- 4. The "Summarizer" Chain ---
+# --- 4. The "Summarizer" Chain ---
 
 def get_summarizer_chain():
     """
     Returns a chain that creates a simple, human-readable summary of a change
-    for logging purposes, in the format you requested.
+    for logging purposes.
     """
     system_prompt = """
-    You are a technical project manager who writes concise, formal changelogs.
-    Based on the provided analysis and git diff, produce a single sentence that
-    describes the change and its impact.
+You are a technical project manager who writes concise, formal changelogs.
+Based on the provided analysis and git diff, produce a single sentence that
+describes the change and its impact.
 
-    Your response MUST be a single sentence that follows the format:
-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
+Your response MUST be a single sentence that follows the format:
+"A push by {user_name} to the file `<file_name>` has <impact_description>."
 
-    - You must determine the most relevant `<file_name>` from the git diff.
-    - You must write the `<impact_description>` based on the AI analysis.
-    - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that" or line numbers.
-    """
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
+    - Keep the `impact_description` brief and high-level.
+    - Do not include "from this to that" or line numbers.
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        CONTEXT:
-        - User: {user_name}
-        - AI Analysis: {analysis_summary}
-        - Git Diff:
-        ```diff
-        {git_diff}
-        ```
-        Please provide the single-sentence summary for the changelog:
-        """)
+CONTEXT:
+- User: {user_name}
+- AI Analysis: {analysis_summary}
+- Git Diff:
+```diff
+{git_diff}
+```
+Please provide the single-sentence summary for the changelog:
+ """)
     ])
     
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 5. The "Seeder" Chain (NEW) ---
-# --- 5. The "Seeder" Chain ---
+# --- 5. The "Seeder" Chain ---
 
 def get_seeder_chain():
     """
@@ -162,31 +168,31 @@ def get_seeder_chain():
     to seed the knowledge base.
     """
     system_prompt = """
-    You are an expert technical writer tasked with creating a high-level project overview
-    to serve as the initial knowledge base for a software project.
+You are an expert technical writer tasked with creating a high-level project overview
+to serve as the initial knowledge base for a software project.
 
-    You will be given the concatenated source code of the project's key files.
+You will be given the concatenated source code of the project's key files.
 
-    Your job is to write a "README" style document that explains:
-    1.  What the project is and its main purpose.
-    2.  The core technologies used.
-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
+Your job is to write a "README" style document that explains:
+1. What the project is and its main purpose.
+2. The core technologies used.
+3. A brief explanation of how the main components work together.
 
-    The output should be in Markdown format and serve as a good starting point for project documentation.
-    Do not add commentary like "Here is the new documentation:".
-    """
+The output should be in Markdown format and serve as a good starting point for project documentation.
+Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the source code of the project:
-        
-        ```python
-        {source_code}
-        ```
-        
-        Please generate the initial project documentation based on this code.
-        """)
+Here is the source code of the project:
+
+```python
+{source_code}
+```
+
+Please generate the initial project documentation based on this code.
+ """)
     ])
     
     seeder_chain = prompt | llm | StrOutputParser()
@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
 # --- Self-Test ---
 if __name__ == "__main__":
     
-    print("--- Running LLM Clients Self-Test ---")
+    print("=" * 70)
+    print("Running Complete Doc-Ops LLM Chains Self-Test")
+    print("=" * 70)
     
-    # Test data
-    test_diff_functional = """
-    --- a/api/routes.py
-    +++ b/api/routes.py
-    @@ -10,5 +10,6 @@
-     @app.route('/api/v1/users')
-     def get_users():
-         return jsonify(users)
-    +
-    +@app.route('/api/v1/users/profile')
-    +def get_user_profile():
-    +    return jsonify({"name": "Test User", "status": "active"})
-    """
-     
-    # 1. Test Analyzer Chain
-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
+    # Test diffs
+    test_diff_functional = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -10,5 +10,6 @@
+ @app.route('/api/v1/users')
+ def get_users():
+     return jsonify(users)
++
++@app.route('/api/v1/users/profile')
++def get_user_profile():
++    return jsonify({"name": "Test User", "status": "active"})
+"""
+
+    test_diff_trivial = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -1,3 +1,4 @@
+ # This file contains all API routes for our app.
+ from flask import Flask, jsonify
+
++# TODO: Add more routes later
+"""
+
+    # 1. Test Analyzer Chain (Functional Change)
+    print("\n" + "-" * 70)
+    print("Test 1: Analyzer Chain (Functional Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_functional = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -10,5 +10,6 @@
-         @app.route('/api/v1/users')
-         def get_users():
-             return jsonify(users)
-        +
-        +@app.route('/api/v1/users/profile')
-        +def get_user_profile():
-        +    return jsonify({"name": "Test User", "status": "active"})
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_functional})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == True
-        print("Test Passed.")
+        print("✅ Test 1 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
+        print(f"❌ Test 1 Failed: {e}")
+        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+
+    # 2. Test Analyzer Chain (Trivial Change)
+    print("\n" + "-" * 70)
+    print("Test 2: Analyzer Chain (Trivial Change)")
+    print("-" * 70)
+    try:
+        analyzer = get_analyzer_chain()
+        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+        print(f"Response:\n{analysis}")
+        assert analysis['is_functional_change'] == False
+        print("✅ Test 2 Passed!")
+    except Exception as e:
+        print(f"❌ Test 2 Failed: {e}")
+
+    # 3. Test Rewriter Chain
+    print("\n" + "-" * 70)
+    print("Test 3: Rewriter Chain")
+    print("-" * 70)
+    try:
+        rewriter = get_rewriter_chain()
+        test_old_docs = [
+            Document(
+                page_content="Our API has one user endpoint: /api/v1/users.", 
+                metadata={"source": "api.md"}
+            )
+        ]
+        formatted_docs = format_docs_for_context(test_old_docs)
+        
+        rewrite = rewriter.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "old_docs_context": formatted_docs,
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{rewrite}")
+        assert "/api/v1/users/profile" in rewrite
+        print("✅ Test 3 Passed!")
+    except Exception as e:
+        print(f"❌ Test 3 Failed: {e}")
+
+    # 4. Test Creator Chain
+    print("\n" + "-" * 70)
+    print("Test 4: Creator Chain (New Documentation)")
+    print("-" * 70)
+    try:
+        creator = get_creator_chain()
+        new_docs = creator.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{new_docs}")
+        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
+        print("✅ Test 4 Passed!")
+    except Exception as e:
+        print(f"❌ Test 4 Failed: {e}")
+
+    # 5. Test Summarizer Chain
+    print("\n" + "-" * 70)
+    print("Test 5: Summarizer Chain (Changelog)")
+    print("-" * 70)
+    try:
+        summarizer = get_summarizer_chain()
+        summary = summarizer.invoke({
+            "user_name": "john_doe",
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{summary}")
+        assert "john_doe" in summary or "api/routes.py" in summary
+        print("✅ Test 5 Passed!")
+    except Exception as e:
+        print(f"❌ Test 5 Failed: {e}")
+
+    # 6. Test Seeder Chain
+    print("\n" + "-" * 70)
+    print("Test 6: Seeder Chain (Initial Project Documentation)")
+    print("-" * 70)
+    try:
+        seeder = get_seeder_chain()
+        test_source_code = """
+from flask import Flask, jsonify
+
+app = Flask(__name__)
+
+@app.route('/api/v1/users')
+def get_users():
+    return jsonify({'users': ['Alice', 'Bob']})
+
+if __name__ == '__main__':
+    app.run(debug=True)
+"""
+        seed_docs = seeder.invoke({"source_code": test_source_code})
+        print(f"Response:\n{seed_docs}")
+        assert "Flask" in seed_docs or "API" in seed_docs
+        print("✅ Test 6 Passed!")
+    except Exception as e:
+        print(f"❌ Test 6 Failed: {e}")
+    
+    # Final Summary
+    print("\n" + "=" * 70)
+    print("Self-Test Complete!")
+    print("=" * 70)
+    print("\n💡 All chains are ready to use:")
+    print("   1. Analyzer Chain - Detects functional vs trivial changes")
+    print("   2. Rewriter Chain - Updates existing documentation")
+    print("   3. Creator Chain - Creates new documentation from scratch")
+    print("   4. Summarizer Chain - Generates changelog summaries")
+    print("   5. Seeder Chain - Creates initial project documentation")
+    print("=" * 70)
+
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
+++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
+++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
+++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
+++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
+++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
+index 629049c..6fc069a 100644
+--- a/backend/USER_GUIDE.md
++++ b/backend/USER_GUIDE.md
+@@ -1,10 +1,10 @@
+-# Doc-Ops Agent: User & Setup Guide
++# DocSmith: User & Setup Guide
+ 
+-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+ 
+ ## 1. Overview
+ 
+-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+ 
+ 1.  **Analyzes the code diff** using an AI model (OpenAI).
+ 2.  **Determines if the change is significant** enough to warrant a documentation update.
+@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
+ 
+ ## 2. Core Technologies
+ 
+-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
+ *   **Frontend**: React, Server-Sent Events (SSE) for live logging
+ *   **Vector Store**: FAISS for efficient similarity search
+ 
+@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
+ -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
+ -   **Git**: [Download Git](https://git-scm.com/downloads/)
+ -   **GitHub Account**: You will need a personal GitHub account.
+-*   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
+ -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
+ 
+ ## 4. Setup and Installation
+@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
+     # Your GitHub Personal Access Token for API actions
+     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
+ 
+-    # Your OpenAI API key
+-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
++    # Your Google AI API key for Gemini
++    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
+ 
+     # (Optional) The minimum confidence score required to update a document
+     CONFIDENCE_THRESHOLD=0.2
+@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
+ 2.  Click **Generate new token** (or **Generate new token (classic)**).
+-*   Give it a descriptive name (e.g., "Doc-Ops Agent").
++*   Give it a descriptive name (e.g., "DocSmith").
+  4.  Set the **Expiration** as needed (e.g., 90 days).
+  5.  Select the following **scopes**:
+      *   `repo` (Full control of private repositories)
+@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
+ 
+-#### OpenAI API Key (`OPENAI_API_KEY`)
++#### Google AI API Key (`GOOGLE_API_KEY`)
+ 
+ 1.  Log in to your OpenAI Platform account.
+ 2.  Go to the **API Keys** section.
+@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
+ 
+ ## 8. How to Use the Agent
+ 
+-Your setup is complete! Now you can test the agent's workflow.
++Your setup is complete! Now you can test DocSmith's workflow.
+ 
+ 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
+ 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
+ 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
+ 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
+-*   **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
++*   **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
+  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
+ 
+  ---
+ 
+-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+ 
+ ## 9. Deployment to Render
+ 
+-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
+ 
+  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
+  2.  **Configure the service** with the following settings:
+@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
+          *   Use the port recommended by Render (e.g., `10000`).
+   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
+-*   **Deploy**: Trigger a manual deploy.
++*   **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+  Your agent is now live and will run automatically in the cloud!
+@@ -211,4 +211,23 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+  4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+-Your agent is now live and will run automatically in the cloud!
+\ No newline at end of file
++Your agent is now live and will run automatically in the cloud!
++
++## 10. Deployment (Frontend to Vercel)
++
++To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.
++
++1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
++2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
++3.  **Configure Project**:
++    *   Vercel will automatically detect that it's a Create React App.
++    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
++4.  **Configure Environment Variables**:
++    *   This is the most important step. Expand the "Environment Variables" section.
++    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
++    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
++5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.
++
++---
++
++You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!
+\ No newline at end of file
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 28f6635..0e5420a 100644
+--- a/backend/data/@Knowledge_base.md
++++ b/backend/data/@Knowledge_base.md
+@@ -1122,3 +1122,1393 @@ index f422459..4556d9d 100644
+ Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
+ 
+ ```
++
++
++---
++
++### AI-Generated Update (2025-11-16 15:56:55)
++
++# DocSmith: User & Setup Guide
++
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++
++## 1. Overview
++
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++
++1.  **Analyzes the code diff** using an AI model (Google Gemini).
++2.  **Determines if the change is significant** enough to warrant a documentation update.
++3.  **Retrieves relevant existing documentation** snippets from a vector store.
++4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
++5.  **Creates a new pull request** with the documentation changes.
++
++## 2. Core Technologies
++
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
++*   **Frontend**: React, Server-Sent Events (SSE) for live logging
++*   **Vector Store**: FAISS for efficient similarity search
++
++## 3. Prerequisites
++
++Before you begin, ensure you have the following installed and configured:
++
++*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
++*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
++*   **Git**: [Download Git](https://git-scm.com/downloads/)
++*   **GitHub Account**: You will need a personal GitHub account.
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
++*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
++
++## 4. Setup and Installation
++
++1.  **Clone the Repository**:
++    ```bash
++    git clone https://github.com/livingcool/doc-ops-agent.git
++    cd doc-ops-agent
++    ```
++
++2.  **Set up Backend Environment**:
++    *   Create a virtual environment:
++        ```bash
++        python -m venv venv
++        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
++        ```
++    *   Install Python dependencies:
++        ```bash
++        pip install -r requirements.txt
++        ```
++    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
++        ```dotenv
++        # .env file in backend/ directory
++        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
++        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
++        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
++        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
++        ```
++
++3.  **Set up Frontend Environment**:
++    *   Navigate to the `frontend/` directory:
++        ```bash
++        cd frontend
++        ```
++    *   Install Node.js dependencies:
++        ```bash
++        npm install
++        ```
++
++4.  **Initialize the Vector Store**:
++    *   Run the Python script to load initial documentation (if any) into the FAISS index:
++        ```bash
++        python ../backend/vector_store.py
++        ```
++        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.
++
++## 5. Configuration
++
++### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)
++
++The agent needs this token to create branches and pull requests on your behalf.
++
++1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
++2.  Click **Generate new token** (or **Generate new token (classic)**).
++3.  Give it a descriptive name (e.g., "DocSmith").
++4.  Set the **Expiration** as needed (e.g., 90 days).
++5.  Select the following **scopes**:
++    *   `repo` (Full control of private repositories)
++    *   `admin:repo_hook` (Full control of repository hooks)
++6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.
++
++### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)
++
++This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.
++
++### 5.3 Google AI API Key (`GOOGLE_API_KEY`)
++
++1.  Log in to your Google AI Studio account.
++2.  Go to the **API Key** section.
++3.  Create a new API key or use an existing one.
++4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.
++
++### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)
++
++This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.
++
++## 6. Running the Application
++
++1.  **Start the Backend Server**:
++    *   Activate your backend virtual environment (`source venv/bin/activate`).
++    *   Run the FastAPI application:
++        ```bash
++        cd backend
++        uvicorn main:app --reload --port 8000
++        ```
++
++2.  **Start the Frontend Development Server**:
++    *   Open a new terminal.
++    *   Navigate to the `frontend/` directory.
++    *   Run the React development server:
++        ```bash
++        cd frontend
++        npm start
++        ```
++    *   The frontend will be available at `http://localhost:3000`.
++
++3.  **Expose your Local Server with ngrok**:
++    *   Open another terminal.
++    *   Run ngrok to expose your local backend server to the internet:
++        ```bash
++        ngrok http 8000
++        ```
++    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).
++
++4.  **Configure GitHub Webhook**:
++    *   Go to your GitHub repository's **Settings** > **Webhooks**.
++    *   Click **Add webhook**.
++    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
++    *   **Content type**: Select `application/json`.
++    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
++    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
++    *   Ensure **Active** is checked.
++    *   Click **Add webhook**.
++
++## 7. How to Use DocSmith
++
++Your setup is complete! Now you can test DocSmith's workflow.
++
++1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
++2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
++3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
++4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
++5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
++6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
++
++---
++
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++
++## 8. Deployment to Render
++
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
++
++1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
++2.  **Configure the service** with the following settings:
++    *   **Build Command**: `pip install -r requirements.txt`
++    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
++        *   Use the port recommended by Render (e.g., `10000`).
++3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
++4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
++5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
++
++Your agent is now live and will run automatically in the cloud!
++
++---
++
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
++++def _extract_changed_lines(git_diff: str) -> str:
++++    """A helper to extract only the added/modified lines from a git diff."""
++++    changed_lines = []
++++    for line in git_diff.split('\n'):
++++        # We only care about lines that were added.
++++        if line.startswith('+') and not line.startswith('+++'):
++++            changed_lines.append(line[1:]) # Remove the '+'
++++    
++++    return "\n".join(changed_lines)
++++
 + # --- Updated Core Agent Logic ---
 + 
 + async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
++++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++++        concise_diff = _extract_changed_lines(git_diff)
++++        if not concise_diff:
++++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++++            return
++++
 +         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
 -        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
 
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff # Use the concise diff here as well
         })
         # Broadcast the clean summary instead of the raw analysis
         await broadcaster("log-summary", human_readable_summary)
@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
             new_documentation = await creator_chain.ainvoke({
                 "analysis_summary": analysis_summary,
-                "git_diff": git_diff
+                "git_diff": concise_diff # Use the concise diff
             })
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
             if confidence_score > 0:
@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             new_documentation = await rewriter_chain.ainvoke({
                 "analysis_summary": analysis_summary,
                 "old_docs_context": old_docs_context,
-                "git_diff": git_diff
+                "git_diff": git_diff # The rewriter gets the full diff for context
             })
             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
 
@@ -222,8 +238,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
+        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index 4fb803e..dcfa93c 100644
--- a/backend/data/@Knowledge_base.md
++++++ b/backend/data/@Knowledge_base.md
@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
  def get_seeder_chain():
      """
  ```
++++
++++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
++++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
++++++    get_summarizer_chain,
++++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
++++++    creator_chain = get_creator_chain()
++++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
++++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
++++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
++++++            analysis_summary, k=5
++++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
++++++        retrieved_docs = [doc for doc, score in docs_with_scores]
++++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
++++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
++++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
++++++        pr_body_note = ""
++++++
++++++        if not retrieved_docs or confidence_score < confidence_threshold:
++++++            # CREATE MODE: No relevant docs found or confidence is too low.
++++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
++++++            new_documentation = await creator_chain.ainvoke({
++++++                "analysis_summary": analysis_summary,
++++++                "git_diff": git_diff
++++++            })
++++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
++++++            if confidence_score > 0:
++++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
 +         else:
 +             # UPDATE MODE: High confidence, proceed with rewriting.
 +             await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
@@ -212,8 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
++++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
++++ b/backend/llm_clients.py
@@ -8,9 +8,17 @@
 # --- Load API Key ---
 load_dotenv()
 
+# Check if API key exists
+GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
+if not GOOGLE_API_KEY:
+    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
+
+# Set the API key for the SDK
+os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
+
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-2.5-flash", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
@@ -22,59 +30,57 @@ def get_analyzer_chain():
     """
     
     system_prompt = """
-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
-    and determine if the change is a 'trivial' change (like fixing a typo, 
-    adding comments, or refactoring code) or a 'functional' change 
-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
-
-    You MUST respond in JSON format with two keys:
-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
-
-    Examples:
-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
-    """
+You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
+and determine if the change is a 'trivial' change (like fixing a typo, 
+adding comments, or refactoring code) or a 'functional' change 
+(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+
+You MUST respond in JSON format with two keys:
+1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+
+Examples:
+- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     return analyzer_chain
 
-# --- 2. The "Rewriter" Chain (UPDATED) ---
-# --- 2. The "Rewriter" Chain ---
+# --- 2. The "Rewriter" Chain ---
 
 def get_rewriter_chain():
     """
     Returns a chain that rewrites documentation.
     """
     
-    # --- THIS PROMPT IS UPDATED ---
     system_prompt = """
-    You are an expert technical writer. Your task is to rewrite old documentation 
-    to match the new code changes.
+You are an expert technical writer. Your task is to rewrite old documentation 
+to match the new code changes.
 
-    You will be given:
-    1. The Old Documentation (as a list of relevant snippets).
-    2. The 'git diff' of the new code.
-    3. An analysis of what changed.
+You will be given:
+1. The Old Documentation (as a list of relevant snippets).
+2. The 'git diff' of the new code.
+3. An analysis of what changed.
 
-    Your job is to return the new, rewritten documentation.
-    - Maintain the original tone and formatting (e.g., Markdown).
-    - Do not add commentary like "Here is the new documentation:".
-    
-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
-    the relevant code diff. The final output must be in this format:
-    
-    [Your rewritten documentation text]
-    
-    ---
-    
-    ### Relevant Code Changes
-    ```diff
-    [The exact 'git diff' you were provided]
-    ```
-    """
-    # --- END OF UPDATE ---
+Your job is to return the new, rewritten documentation.
+- Maintain the original tone and formatting (e.g., Markdown).
+- Do not add commentary like "Here is the new documentation:".
+
+**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+the relevant code diff. The final output must be in this format:
+
+[Your rewritten documentation text]
+
+---
+
+### Relevant Code Changes
+```diff
+[The exact 'git diff' you were provided]
+```
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     # We pipe this to the LLM and then to a simple string parser
@@ -82,79 +88,79 @@ def get_rewriter_chain():
     
     return rewriter_chain
 
-# --- 3. The "Creator" Chain (NEW) ---
-# --- 3. The "Creator" Chain ---
+# --- 3. The "Creator" Chain ---
 
 def get_creator_chain():
     """
     Returns a chain that creates a NEW documentation section from scratch
     when no existing documentation is found.
     """
-    system_prompt = """
-    You are an expert technical writer tasked with creating a new documentation
-    section for a feature that has no prior documentation.
-
-    You will be given:
-    1. A 'git diff' of the new code.
-    2. An AI-generated analysis of what changed.
-
-    Your job is to write a clear, concise documentation section explaining the new
-    feature. The output should be ready to be added to a larger document.
-    - Use Markdown formatting.
-    - Explain the feature's purpose and how it works based on the code.
-    - Do not add commentary like "Here is the new documentation:".
-    """
+    system_prompt = """You are an expert technical writer tasked with creating a new documentation
+section for a feature that has no prior documentation.
+
+You will be given:
+1. A 'git diff' of the new code.
+2. An AI-generated analysis of what changed.
+
+Your job is to write a clear, concise documentation section explaining the new
+feature. The output should be ready to be added to a larger document.
+- Use Markdown formatting.
+- Explain the feature's purpose and how it works based on the code.
+- Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context for the new feature:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please write a new documentation section for this feature:
-        """)
+Here is the context for the new feature:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please write a new documentation section for this feature:
+ """)
     ])
     
     creator_chain = prompt | llm | StrOutputParser()
     return creator_chain
 
-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
-# --- 4. The "Summarizer" Chain ---
+# --- 4. The "Summarizer" Chain ---
 
 def get_summarizer_chain():
     """
     Returns a chain that creates a simple, human-readable summary of a change
-    for logging purposes, in the format you requested.
+    for logging purposes.
     """
     system_prompt = """
-    You are a technical project manager who writes concise, formal changelogs.
-    Based on the provided analysis and git diff, produce a single sentence that
-    describes the change and its impact.
+You are a technical project manager who writes concise, formal changelogs.
+Based on the provided analysis and git diff, produce a single sentence that
+describes the change and its impact.
 
-    Your response MUST be a single sentence that follows the format:
-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
+Your response MUST be a single sentence that follows the format:
+"A push by {user_name} to the file `<file_name>` has <impact_description>."
 
-    - You must determine the most relevant `<file_name>` from the git diff.
-    - You must write the `<impact_description>` based on the AI analysis.
-    - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that" or line numbers.
-    """
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
+    - Keep the `impact_description` brief and high-level.
+    - Do not include "from this to that" or line numbers.
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        CONTEXT:
-        - User: {user_name}
-        - AI Analysis: {analysis_summary}
-        - Git Diff:
-        ```diff
-        {git_diff}
-        ```
-        Please provide the single-sentence summary for the changelog:
-        """)
+CONTEXT:
+- User: {user_name}
+- AI Analysis: {analysis_summary}
+- Git Diff:
+```diff
+{git_diff}
+```
+Please provide the single-sentence summary for the changelog:
+ """)
     ])
     
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 5. The "Seeder" Chain (NEW) ---
-# --- 5. The "Seeder" Chain ---
+# --- 5. The "Seeder" Chain ---
 
 def get_seeder_chain():
     """
@@ -162,31 +168,31 @@ def get_seeder_chain():
     to seed the knowledge base.
     """
     system_prompt = """
-    You are an expert technical writer tasked with creating a high-level project overview
-    to serve as the initial knowledge base for a software project.
+You are an expert technical writer tasked with creating a high-level project overview
+to serve as the initial knowledge base for a software project.
 
-    You will be given the concatenated source code of the project's key files.
+You will be given the concatenated source code of the project's key files.
 
-    Your job is to write a "README" style document that explains:
-    1.  What the project is and its main purpose.
-    2.  The core technologies used.
-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
+Your job is to write a "README" style document that explains:
+1. What the project is and its main purpose.
+2. The core technologies used.
+3. A brief explanation of how the main components work together.
 
-    The output should be in Markdown format and serve as a good starting point for project documentation.
-    Do not add commentary like "Here is the new documentation:".
-    """
+The output should be in Markdown format and serve as a good starting point for project documentation.
+Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the source code of the project:
-        
-        ```python
-        {source_code}
-        ```
-        
-        Please generate the initial project documentation based on this code.
-        """)
+Here is the source code of the project:
+
+```python
+{source_code}
+```
+
+Please generate the initial project documentation based on this code.
+ """)
     ])
     
     seeder_chain = prompt | llm | StrOutputParser()
@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
 # --- Self-Test ---
 if __name__ == "__main__":
     
-    print("--- Running LLM Clients Self-Test ---")
+    print("=" * 70)
+    print("Running Complete Doc-Ops LLM Chains Self-Test")
+    print("=" * 70)
     
-    # Test data
-    test_diff_functional = """
-    --- a/api/routes.py
-    +++ b/api/routes.py
-    @@ -10,5 +10,6 @@
-     @app.route('/api/v1/users')
-     def get_users():
-         return jsonify(users)
-    +
-    +@app.route('/api/v1/users/profile')
-    +def get_user_profile():
-    +    return jsonify({"name": "Test User", "status": "active"})
-    """
-     
-    # 1. Test Analyzer Chain
-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
+    # Test diffs
+    test_diff_functional = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -10,5 +10,6 @@
+ @app.route('/api/v1/users')
+ def get_users():
+     return jsonify(users)
++
++@app.route('/api/v1/users/profile')
++def get_user_profile():
++    return jsonify({"name": "Test User", "status": "active"})
+"""
+
+    test_diff_trivial = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -1,3 +1,4 @@
+ # This file contains all API routes for our app.
+ from flask import Flask, jsonify
+
++# TODO: Add more routes later
+"""
+
+    # 1. Test Analyzer Chain (Functional Change)
+    print("\n" + "-" * 70)
+    print("Test 1: Analyzer Chain (Functional Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_functional = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -10,5 +10,6 @@
-         @app.route('/api/v1/users')
-         def get_users():
-             return jsonify(users)
-        +
-        +@app.route('/api/v1/users/profile')
-        +def get_user_profile():
-        +    return jsonify({"name": "Test User", "status": "active"})
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_functional})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == True
-        print("Test Passed.")
+        print("✅ Test 1 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
+        print(f"❌ Test 1 Failed: {e}")
+        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+
+    # 2. Test Analyzer Chain (Trivial Change)
+    print("\n" + "-" * 70)
+    print("Test 2: Analyzer Chain (Trivial Change)")
+    print("-" * 70)
+    try:
+        analyzer = get_analyzer_chain()
+        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+        print(f"Response:\n{analysis}")
+        assert analysis['is_functional_change'] == False
+        print("✅ Test 2 Passed!")
+    except Exception as e:
+        print(f"❌ Test 2 Failed: {e}")
+
+    # 3. Test Rewriter Chain
+    print("\n" + "-" * 70)
+    print("Test 3: Rewriter Chain")
+    print("-" * 70)
+    try:
+        rewriter = get_rewriter_chain()
+        test_old_docs = [
+            Document(
+                page_content="Our API has one user endpoint: /api/v1/users.", 
+                metadata={"source": "api.md"}
+            )
+        ]
+        formatted_docs = format_docs_for_context(test_old_docs)
+        
+        rewrite = rewriter.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "old_docs_context": formatted_docs,
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{rewrite}")
+        assert "/api/v1/users/profile" in rewrite
+        print("✅ Test 3 Passed!")
+    except Exception as e:
+        print(f"❌ Test 3 Failed: {e}")
+
+    # 4. Test Creator Chain
+    print("\n" + "-" * 70)
+    print("Test 4: Creator Chain (New Documentation)")
+    print("-" * 70)
+    try:
+        creator = get_creator_chain()
+        new_docs = creator.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{new_docs}")
+        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
+        print("✅ Test 4 Passed!")
+    except Exception as e:
+        print(f"❌ Test 4 Failed: {e}")
+
+    # 5. Test Summarizer Chain
+    print("\n" + "-" * 70)
+    print("Test 5: Summarizer Chain (Changelog)")
+    print("-" * 70)
+    try:
+        summarizer = get_summarizer_chain()
+        summary = summarizer.invoke({
+            "user_name": "john_doe",
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{summary}")
+        assert "john_doe" in summary or "api/routes.py" in summary
+        print("✅ Test 5 Passed!")
+    except Exception as e:
+        print(f"❌ Test 5 Failed: {e}")
+
+    # 6. Test Seeder Chain
+    print("\n" + "-" * 70)
+    print("Test 6: Seeder Chain (Initial Project Documentation)")
+    print("-" * 70)
+    try:
+        seeder = get_seeder_chain()
+        test_source_code = """
+from flask import Flask, jsonify
+
+app = Flask(__name__)
+
+@app.route('/api/v1/users')
+def get_users():
+    return jsonify({'users': ['Alice', 'Bob']})
+
+if __name__ == '__main__':
+    app.run(debug=True)
+"""
+        seed_docs = seeder.invoke({"source_code": test_source_code})
+        print(f"Response:\n{seed_docs}")
+        assert "Flask" in seed_docs or "API" in seed_docs
+        print("✅ Test 6 Passed!")
+    except Exception as e:
+        print(f"❌ Test 6 Failed: {e}")
+    
+    # Final Summary
+    print("\n" + "=" * 70)
+    print("Self-Test Complete!")
+    print("=" * 70)
+    print("\n💡 All chains are ready to use:")
+    print("   1. Analyzer Chain - Detects functional vs trivial changes")
+    print("   2. Rewriter Chain - Updates existing documentation")
+    print("   3. Creator Chain - Creates new documentation from scratch")
+    print("   4. Summarizer Chain - Generates changelog summaries")
+    print("   5. Seeder Chain - Creates initial project documentation")
+    print("=" * 70)
+
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
+++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
+++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
+++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
+++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
+++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
+index 629049c..6fc069a 100644
+--- a/backend/USER_GUIDE.md
++++ b/backend/USER_GUIDE.md
+@@ -1,10 +1,10 @@
+-# Doc-Ops Agent: User & Setup Guide
++# DocSmith: User & Setup Guide
+ 
+-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+ 
+ ## 1. Overview
+ 
+-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+ 
+ 1.  **Analyzes the code diff** using an AI model (OpenAI).
+ 2.  **Determines if the change is significant** enough to warrant a documentation update.
+@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
+ 
+ ## 2. Core Technologies
+ 
+-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
+ *   **Frontend**: React, Server-Sent Events (SSE) for live logging
+ *   **Vector Store**: FAISS for efficient similarity search
+ 
+@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
+ -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
+ -   **Git**: [Download Git](https://git-scm.com/downloads/)
+ -   **GitHub Account**: You will need a personal GitHub account.
+-*   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
+ -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
+ 
+ ## 4. Setup and Installation
+@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
+     # Your GitHub Personal Access Token for API actions
+     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
+ 
+-    # Your OpenAI API key
+-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
++    # Your Google AI API key for Gemini
++    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
+ 
+     # (Optional) The minimum confidence score required to update a document
+     CONFIDENCE_THRESHOLD=0.2
+@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
+ 2.  Click **Generate new token** (or **Generate new token (classic)**).
+-*   Give it a descriptive name (e.g., "Doc-Ops Agent").
++*   Give it a descriptive name (e.g., "DocSmith").
+  4.  Set the **Expiration** as needed (e.g., 90 days).
+  5.  Select the following **scopes**:
+      *   `repo` (Full control of private repositories)
+@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
+ 
+-#### OpenAI API Key (`OPENAI_API_KEY`)
++#### Google AI API Key (`GOOGLE_API_KEY`)
+ 
+ 1.  Log in to your OpenAI Platform account.
+ 2.  Go to the **API Keys** section.
+@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
+ 
+ ## 8. How to Use the Agent
+ 
+-Your setup is complete! Now you can test the agent's workflow.
++Your setup is complete! Now you can test DocSmith's workflow.
+ 
+ 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
+ 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
+ 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
+ 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
+-*   **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
++*   **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
+  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
+ 
+  ---
+ 
+-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+ 
+ ## 9. Deployment to Render
+ 
+-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
+ 
+  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
+  2.  **Configure the service** with the following settings:
+@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
+          *   Use the port recommended by Render (e.g., `10000`).
+   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
+-*   **Deploy**: Trigger a manual deploy.
++*   **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+  Your agent is now live and will run automatically in the cloud!
+@@ -211,4 +211,23 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+  4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+-Your agent is now live and will run automatically in the cloud!
+\ No newline at end of file
++Your agent is now live and will run automatically in the cloud!
++
++## 10. Deployment (Frontend to Vercel)
++
++To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.
++
++1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
++2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
++3.  **Configure Project**:
++    *   Vercel will automatically detect that it's a Create React App.
++    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
++4.  **Configure Environment Variables**:
++    *   This is the most important step. Expand the "Environment Variables" section.
++    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
++    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
++5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.
++
++---
++
++You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!
+\ No newline at end of file
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 28f6635..0e5420a 100644
+--- a/backend/data/@Knowledge_base.md
++++ b/backend/data/@Knowledge_base.md
+@@ -1122,3 +1122,1393 @@ index f422459..4556d9d 100644
+ Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
+ 
+ ```
++
++
++---
++
++### AI-Generated Update (2025-11-16 15:56:55)
++
++# DocSmith: User & Setup Guide
++
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++
++## 1. Overview
++
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++
++1.  **Analyzes the code diff** using an AI model (Google Gemini).
++2.  **Determines if the change is significant** enough to warrant a documentation update.
++3.  **Retrieves relevant existing documentation** snippets from a vector store.
++4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
++5.  **Creates a new pull request** with the documentation changes.
++
++## 2. Core Technologies
++
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
++*   **Frontend**: React, Server-Sent Events (SSE) for live logging
++*   **Vector Store**: FAISS for efficient similarity search
++
++## 3. Prerequisites
++
++Before you begin, ensure you have the following installed and configured:
++
++*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
++*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
++*   **Git**: [Download Git](https://git-scm.com/downloads/)
++*   **GitHub Account**: You will need a personal GitHub account.
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
++*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
++
++## 4. Setup and Installation
++
++1.  **Clone the Repository**:
++    ```bash
++    git clone https://github.com/livingcool/doc-ops-agent.git
++    cd doc-ops-agent
++    ```
++
++2.  **Set up Backend Environment**:
++    *   Create a virtual environment:
++        ```bash
++        python -m venv venv
++        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
++        ```
++    *   Install Python dependencies:
++        ```bash
++        pip install -r requirements.txt
++        ```
++    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
++        ```dotenv
++        # .env file in backend/ directory
++        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
++        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
++        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
++        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
++        ```
++
++3.  **Set up Frontend Environment**:
++    *   Navigate to the `frontend/` directory:
++        ```bash
++        cd frontend
++        ```
++    *   Install Node.js dependencies:
++        ```bash
++        npm install
++        ```
++
++4.  **Initialize the Vector Store**:
++    *   Run the Python script to load initial documentation (if any) into the FAISS index:
++        ```bash
++        python ../backend/vector_store.py
++        ```
++        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.
++
++## 5. Configuration
++
++### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)
++
++The agent needs this token to create branches and pull requests on your behalf.
++
++1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
++2.  Click **Generate new token** (or **Generate new token (classic)**).
++3.  Give it a descriptive name (e.g., "DocSmith").
++4.  Set the **Expiration** as needed (e.g., 90 days).
++5.  Select the following **scopes**:
++    *   `repo` (Full control of private repositories)
++    *   `admin:repo_hook` (Full control of repository hooks)
++6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.
++
++### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)
++
++This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.
++
++### 5.3 Google AI API Key (`GOOGLE_API_KEY`)
++
++1.  Log in to your Google AI Studio account.
++2.  Go to the **API Key** section.
++3.  Create a new API key or use an existing one.
++4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.
++
++### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)
++
++This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.
++
++## 6. Running the Application
++
++1.  **Start the Backend Server**:
++    *   Activate your backend virtual environment (`source venv/bin/activate`).
++    *   Run the FastAPI application:
++        ```bash
++        cd backend
++        uvicorn main:app --reload --port 8000
++        ```
++
++2.  **Start the Frontend Development Server**:
++    *   Open a new terminal.
++    *   Navigate to the `frontend/` directory.
++    *   Run the React development server:
++        ```bash
++        cd frontend
++        npm start
++        ```
++    *   The frontend will be available at `http://localhost:3000`.
++
++3.  **Expose your Local Server with ngrok**:
++    *   Open another terminal.
++    *   Run ngrok to expose your local backend server to the internet:
++        ```bash
++        ngrok http 8000
++        ```
++    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).
++
++4.  **Configure GitHub Webhook**:
++    *   Go to your GitHub repository's **Settings** > **Webhooks**.
++    *   Click **Add webhook**.
++    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
++    *   **Content type**: Select `application/json`.
++    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
++    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
++    *   Ensure **Active** is checked.
++    *   Click **Add webhook**.
++
++## 7. How to Use DocSmith
++
++Your setup is complete! Now you can test DocSmith's workflow.
++
++1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
++2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
++3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
++4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
++5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
++6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
++
++---
++
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++
++## 8. Deployment to Render
++
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
++
++1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
++2.  **Configure the service** with the following settings:
++    *   **Build Command**: `pip install -r requirements.txt`
++    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
++        *   Use the port recommended by Render (e.g., `10000`).
++3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
++4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
++5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
++
++Your agent is now live and will run automatically in the cloud!
++
++---
+
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
++++def _extract_changed_lines(git_diff: str) -> str:
++++    """A helper to extract only the added/modified lines from a git diff."""
++++    changed_lines = []
++++    for line in git_diff.split('\n'):
++++        # We only care about lines that were added.
++++        if line.startswith('+') and not line.startswith('+++'):
++++            changed_lines.append(line[1:]) # Remove the '+'
++++    
++++    return "\n".join(changed_lines)
++++
 + # --- Updated Core Agent Logic ---
 + 
 + async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
++++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++++        concise_diff = _extract_changed_lines(git_diff)
++++        if not concise_diff:
++++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++++            return
++++
 +         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
 -        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
 
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff # Use the concise diff here as well
         })
         # Broadcast the clean summary instead of the raw analysis
         await broadcaster("log-summary", human_readable_summary)
@@ -201,7 +217,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
             new_documentation = await creator_chain.ainvoke({
                 "analysis_summary": analysis_summary,
-                "git_diff": git_diff
+                "git_diff": concise_diff # Use the concise diff
             })
             raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
             if confidence_score > 0:
@@ -213,7 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
             new_documentation = await rewriter_chain.ainvoke({
                 "analysis_summary": analysis_summary,
                 "old_docs_context": old_docs_context,
-                "git_diff": git_diff
+                "git_diff": git_diff # The rewriter gets the full diff for context
             })
             raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
 
@@ -222,8 +238,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
+        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
index 4fb803e..dcfa93c 100644
--- a/backend/data/@Knowledge_base.md
++++++ b/backend/data/@Knowledge_base.md
@@ -160,3 +160,530 @@ index 0213b43..80fa1ee 100644
  def get_seeder_chain():
      """
  ```
++++
++++
+---
+
+### AI-Generated Update (2025-11-16 14:24:06)
+
+---
+
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index a129961..7453050 100644
+--- a/backend/agent_logic.py
++++++++ b/backend/agent_logic.py
+@@ -10,7 +10,8 @@
+     get_analyzer_chain, 
+     get_rewriter_chain, 
+     format_docs_for_context,
+-    get_summarizer_chain # <-- IMPORT THE NEW CHAIN
++++++    get_summarizer_chain,
++++++    get_creator_chain
+ )
+ from vector_store import get_retriever, add_docs_to_store
+ 
+@@ -23,11 +24,12 @@
+     retriever = get_retriever()
+     analyzer_chain = get_analyzer_chain()
+     rewriter_chain = get_rewriter_chain()
+-    summarizer_chain = get_summarizer_chain() # <-- INITIALIZE THE NEW CHAIN
++++++    creator_chain = get_creator_chain()
++++++    summarizer_chain = get_summarizer_chain()
+     print("✅ AI components are ready.")
+ except Exception as e:
+     print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
+ -    retriever, analyzer_chain, rewriter_chain, summarizer_chain = None, None, None, None
++++++    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None
+ 
+ # --- GitHub PR Creation Logic (Synchronous) ---
+ def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
+@@ -177,34 +179,43 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
+         # --- Step 3: Retrieve relevant old docs ---
+         await broadcaster("log-step", "Functional change. Searching for relevant docs...")
+         # Use `aget_relevant_documents` which returns scores with FAISS
+-        retrieved_docs = await retriever.aget_relevant_documents(analysis_summary)
++++++        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
++++++            analysis_summary, k=5
++++++        )
+         
+-        # --- THIS IS THE FIX ---
+-        # The score is in the metadata when using FAISS with similarity_score_threshold
+-        scores = [doc.metadata.get('score', 0.0) for doc in retrieved_docs]
++++++        retrieved_docs = [doc for doc, score in docs_with_scores]
++++++        scores = [score for doc, score in docs_with_scores]
+         
+         # Calculate confidence score (highest similarity)
+         confidence_score = max(scores) if scores else 0.0
+         confidence_percent = f"{confidence_score * 100:.1f}%"
+ 
+         await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
+-        
+-        if not retrieved_docs:
+-            await broadcaster("log-skip", "No relevant docs found to update.")
+-            return
+-        
+-        if confidence_score < 0.5: # Gatekeeping based on confidence
+-            await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc generation.")
+-            return
+-        old_docs_context = format_docs_for_context(retrieved_docs)
+- 
+-        # --- Step 4: Rewrite the docs ---
+-        await broadcaster("log-step", "Generating new documentation with LLM...")
+-        new_documentation = await rewriter_chain.ainvoke({
+-            "analysis_summary": analysis_summary,
+-            "old_docs_context": old_docs_context,
+-            "git_diff": git_diff
+-        })
++++++        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
++++++        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
++++++        pr_body_note = ""
++++++
++++++        if not retrieved_docs or confidence_score < confidence_threshold:
++++++            # CREATE MODE: No relevant docs found or confidence is too low.
++++++            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
++++++            new_documentation = await creator_chain.ainvoke({
++++++                "analysis_summary": analysis_summary,
++++++                "git_diff": git_diff
++++++            })
++++++            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
++++++            if confidence_score > 0:
++++++                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
 +         else:
 +             # UPDATE MODE: High confidence, proceed with rewriting.
 +             await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
@@ -212,8 +229,7 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
         # The agent now "remembers" what it wrote by adding it to the central guide.
         await update_knowledge_base(logger, broadcaster, new_documentation)
 
-        # --- Step 6: Incrementally update the vector store (More Efficient) ---
-        # Instead of rebuilding, we add the new doc directly to the index.
++++++        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
         await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
         new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
         await asyncio.to_thread(add_docs_to_store, [new_doc])
@@ -241,7 +256,10 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
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
++++ b/backend/llm_clients.py
@@ -8,9 +8,17 @@
 # --- Load API Key ---
 load_dotenv()
 
+# Check if API key exists
+GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
+if not GOOGLE_API_KEY:
+    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
+
+# Set the API key for the SDK
+os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
+
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-2.5-flash", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
@@ -22,59 +30,57 @@ def get_analyzer_chain():
     """
     
     system_prompt = """
-    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
-    and determine if the change is a 'trivial' change (like fixing a typo, 
-    adding comments, or refactoring code) or a 'functional' change 
-    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).
-
-    You MUST respond in JSON format with two keys:
-    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
-    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
-       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
-
-    Examples:
-    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
-    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
-    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
-    """
+You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
+and determine if the change is a 'trivial' change (like fixing a typo, 
+adding comments, or refactoring code) or a 'functional' change 
+(like adding a feature, changing an API endpoint, or modifying user-facing behavior).
+
+You MUST respond in JSON format with two keys:
+1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
+2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
+   If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")
+
+Examples:
+- Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
+- Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
+- Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     return analyzer_chain
 
-# --- 2. The "Rewriter" Chain (UPDATED) ---
-# --- 2. The "Rewriter" Chain ---
+# --- 2. The "Rewriter" Chain ---
 
 def get_rewriter_chain():
     """
     Returns a chain that rewrites documentation.
     """
     
-    # --- THIS PROMPT IS UPDATED ---
     system_prompt = """
-    You are an expert technical writer. Your task is to rewrite old documentation 
-    to match the new code changes.
+You are an expert technical writer. Your task is to rewrite old documentation 
+to match the new code changes.
 
-    You will be given:
-    1. The Old Documentation (as a list of relevant snippets).
-    2. The 'git diff' of the new code.
-    3. An analysis of what changed.
+You will be given:
+1. The Old Documentation (as a list of relevant snippets).
+2. The 'git diff' of the new code.
+3. An analysis of what changed.
 
-    Your job is to return the new, rewritten documentation.
-    - Maintain the original tone and formatting (e.g., Markdown).
-    - Do not add commentary like "Here is the new documentation:".
-    
-    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
-    the relevant code diff. The final output must be in this format:
-    
-    [Your rewritten documentation text]
-    
-    ---
-    
-    ### Relevant Code Changes
-    ```diff
-    [The exact 'git diff' you were provided]
-    ```
-    """
-    # --- END OF UPDATE ---
+Your job is to return the new, rewritten documentation.
+- Maintain the original tone and formatting (e.g., Markdown).
+- Do not add commentary like "Here is the new documentation:".
+
+**CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
+the relevant code diff. The final output must be in this format:
+
+[Your rewritten documentation text]
+
+---
+
+### Relevant Code Changes
+```diff
+[The exact 'git diff' you were provided]
+```
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        OLD DOCUMENTATION SNIPPETS:
-        {old_docs_context}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please provide the new, updated documentation based on these changes:
-        """)
+Here is the context:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+OLD DOCUMENTATION SNIPPETS:
+{old_docs_context}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please provide the new, updated documentation based on these changes:
+ """)
     ])
     
     # We pipe this to the LLM and then to a simple string parser
@@ -82,79 +88,79 @@ def get_rewriter_chain():
     
     return rewriter_chain
 
-# --- 3. The "Creator" Chain (NEW) ---
-# --- 3. The "Creator" Chain ---
+# --- 3. The "Creator" Chain ---
 
 def get_creator_chain():
     """
     Returns a chain that creates a NEW documentation section from scratch
     when no existing documentation is found.
     """
-    system_prompt = """
-    You are an expert technical writer tasked with creating a new documentation
-    section for a feature that has no prior documentation.
-
-    You will be given:
-    1. A 'git diff' of the new code.
-    2. An AI-generated analysis of what changed.
-
-    Your job is to write a clear, concise documentation section explaining the new
-    feature. The output should be ready to be added to a larger document.
-    - Use Markdown formatting.
-    - Explain the feature's purpose and how it works based on the code.
-    - Do not add commentary like "Here is the new documentation:".
-    """
+    system_prompt = """You are an expert technical writer tasked with creating a new documentation
+section for a feature that has no prior documentation.
+
+You will be given:
+1. A 'git diff' of the new code.
+2. An AI-generated analysis of what changed.
+
+Your job is to write a clear, concise documentation section explaining the new
+feature. The output should be ready to be added to a larger document.
+- Use Markdown formatting.
+- Explain the feature's purpose and how it works based on the code.
+- Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the context for the new feature:
-        
-        ANALYSIS OF CHANGE:
-        {analysis_summary}
-        
-        CODE CHANGE (GIT DIFF):
-        ```diff
-        {git_diff}
-        ```
-        
-        Please write a new documentation section for this feature:
-        """)
+Here is the context for the new feature:
+
+ANALYSIS OF CHANGE:
+{analysis_summary}
+
+CODE CHANGE (GIT DIFF):
+```diff
+{git_diff}
+```
+
+Please write a new documentation section for this feature:
+ """)
     ])
     
     creator_chain = prompt | llm | StrOutputParser()
     return creator_chain
 
-# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---
-# --- 4. The "Summarizer" Chain ---
+# --- 4. The "Summarizer" Chain ---
 
 def get_summarizer_chain():
     """
     Returns a chain that creates a simple, human-readable summary of a change
-    for logging purposes, in the format you requested.
+    for logging purposes.
     """
     system_prompt = """
-    You are a technical project manager who writes concise, formal changelogs.
-    Based on the provided analysis and git diff, produce a single sentence that
-    describes the change and its impact.
+You are a technical project manager who writes concise, formal changelogs.
+Based on the provided analysis and git diff, produce a single sentence that
+describes the change and its impact.
 
-    Your response MUST be a single sentence that follows the format:
-    "A push by {user_name} to the file `<file_name>` has <impact_description>."
+Your response MUST be a single sentence that follows the format:
+"A push by {user_name} to the file `<file_name>` has <impact_description>."
 
-    - You must determine the most relevant `<file_name>` from the git diff.
-    - You must write the `<impact_description>` based on the AI analysis.
-    - Keep the `impact_description` brief and high-level.
-    - Do not include "from this to that" or line numbers.
-    """
+    - You must determine the most relevant `<file_name>` from the git diff.
+    - You must write the `<impact_description>` based on the AI analysis.
+    - Keep the `impact_description` brief and high-level.
+    - Do not include "from this to that" or line numbers.
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        CONTEXT:
-        - User: {user_name}
-        - AI Analysis: {analysis_summary}
-        - Git Diff:
-        ```diff
-        {git_diff}
-        ```
-        Please provide the single-sentence summary for the changelog:
-        """)
+CONTEXT:
+- User: {user_name}
+- AI Analysis: {analysis_summary}
+- Git Diff:
+```diff
+{git_diff}
+```
+Please provide the single-sentence summary for the changelog:
+ """)
     ])
     
     summarizer_chain = prompt | llm | StrOutputParser()
     return summarizer_chain
 
-# --- 5. The "Seeder" Chain (NEW) ---
-# --- 5. The "Seeder" Chain ---
+# --- 5. The "Seeder" Chain ---
 
 def get_seeder_chain():
     """
@@ -162,31 +168,31 @@ def get_seeder_chain():
     to seed the knowledge base.
     """
     system_prompt = """
-    You are an expert technical writer tasked with creating a high-level project overview
-    to serve as the initial knowledge base for a software project.
+You are an expert technical writer tasked with creating a high-level project overview
+to serve as the initial knowledge base for a software project.
 
-    You will be given the concatenated source code of the project's key files.
+You will be given the concatenated source code of the project's key files.
 
-    Your job is to write a "README" style document that explains:
-    1.  What the project is and its main purpose.
-    2.  The core technologies used.
-    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.
+Your job is to write a "README" style document that explains:
+1. What the project is and its main purpose.
+2. The core technologies used.
+3. A brief explanation of how the main components work together.
 
-    The output should be in Markdown format and serve as a good starting point for project documentation.
-    Do not add commentary like "Here is the new documentation:".
-    """
+The output should be in Markdown format and serve as a good starting point for project documentation.
+Do not add commentary like "Here is the new documentation:".
+ """
 
     prompt = ChatPromptTemplate.from_messages([
         ("system", system_prompt),
         ("human", """
-        Here is the source code of the project:
-        
-        ```python
-        {source_code}
-        ```
-        
-        Please generate the initial project documentation based on this code.
-        """)
+Here is the source code of the project:
+
+```python
+{source_code}
+```
+
+Please generate the initial project documentation based on this code.
+ """)
     ])
     
     seeder_chain = prompt | llm | StrOutputParser()
@@ -211,58 +217,72 @@ def format_docs_for_context(docs: list[Document]) -> str:
 # --- Self-Test ---
 if __name__ == "__main__":
     
-    print("--- Running LLM Clients Self-Test ---")
+    print("=" * 70)
+    print("Running Complete Doc-Ops LLM Chains Self-Test")
+    print("=" * 70)
     
-    # Test data
-    test_diff_functional = """
-    --- a/api/routes.py
-    +++ b/api/routes.py
-    @@ -10,5 +10,6 @@
-     @app.route('/api/v1/users')
-     def get_users():
-         return jsonify(users)
-    +
-    +@app.route('/api/v1/users/profile')
-    +def get_user_profile():
-    +    return jsonify({"name": "Test User", "status": "active"})
-    """
-     
-    # 1. Test Analyzer Chain
-    print("\n--- Testing Analyzer Chain (Functional Change) ---")
+    # Test diffs
+    test_diff_functional = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -10,5 +10,6 @@
+ @app.route('/api/v1/users')
+ def get_users():
+     return jsonify(users)
++
++@app.route('/api/v1/users/profile')
++def get_user_profile():
++    return jsonify({"name": "Test User", "status": "active"})
+"""
+
+    test_diff_trivial = """
+--- a/api/routes.py
++++ b/api/routes.py
+@@ -1,3 +1,4 @@
+ # This file contains all API routes for our app.
+ from flask import Flask, jsonify
+
++# TODO: Add more routes later
+"""
+
+    # 1. Test Analyzer Chain (Functional Change)
+    print("\n" + "-" * 70)
+    print("Test 1: Analyzer Chain (Functional Change)")
+    print("-" * 70)
     try:
         analyzer = get_analyzer_chain()
-        test_diff_functional = """
-        --- a/api/routes.py
-        +++ b/api/routes.py
-        @@ -10,5 +10,6 @@
-         @app.route('/api/v1/users')
-         def get_users():
-             return jsonify(users)
-        +
-        +@app.route('/api/v1/users/profile')
-        +def get_user_profile():
-        +    return jsonify({"name": "Test User", "status": "active"})
-        """
         analysis = analyzer.invoke({"git_diff": test_diff_functional})
         print(f"Response:\n{analysis}")
         assert analysis['is_functional_change'] == True
-        print("Test Passed.")
+        print("✅ Test 1 Passed!")
     except Exception as e:
-        print(f"Test Failed: {e}")
-        print("!! Check if your GOOGLE_API_KEY is set in .env !!")
+        print(f"❌ Test 1 Failed: {e}")
+        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")
+
+    # 2. Test Analyzer Chain (Trivial Change)
+    print("\n" + "-" * 70)
+    print("Test 2: Analyzer Chain (Trivial Change)")
+    print("-" * 70)
+    try:
+        analyzer = get_analyzer_chain()
+        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
+        print(f"Response:\n{analysis}")
+        assert analysis['is_functional_change'] == False
+        print("✅ Test 2 Passed!")
+    except Exception as e:
+        print(f"❌ Test 2 Failed: {e}")
+
+    # 3. Test Rewriter Chain
+    print("\n" + "-" * 70)
+    print("Test 3: Rewriter Chain")
+    print("-" * 70)
+    try:
+        rewriter = get_rewriter_chain()
+        test_old_docs = [
+            Document(
+                page_content="Our API has one user endpoint: /api/v1/users.", 
+                metadata={"source": "api.md"}
+            )
+        ]
+        formatted_docs = format_docs_for_context(test_old_docs)
+        
+        rewrite = rewriter.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "old_docs_context": formatted_docs,
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{rewrite}")
+        assert "/api/v1/users/profile" in rewrite
+        print("✅ Test 3 Passed!")
+    except Exception as e:
+        print(f"❌ Test 3 Failed: {e}")
+
+    # 4. Test Creator Chain
+    print("\n" + "-" * 70)
+    print("Test 4: Creator Chain (New Documentation)")
+    print("-" * 70)
+    try:
+        creator = get_creator_chain()
+        new_docs = creator.invoke({
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{new_docs}")
+        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
+        print("✅ Test 4 Passed!")
+    except Exception as e:
+        print(f"❌ Test 4 Failed: {e}")
+
+    # 5. Test Summarizer Chain
+    print("\n" + "-" * 70)
+    print("Test 5: Summarizer Chain (Changelog)")
+    print("-" * 70)
+    try:
+        summarizer = get_summarizer_chain()
+        summary = summarizer.invoke({
+            "user_name": "john_doe",
+            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
+            "git_diff": test_diff_functional
+        })
+        print(f"Response:\n{summary}")
+        assert "john_doe" in summary or "api/routes.py" in summary
+        print("✅ Test 5 Passed!")
+    except Exception as e:
+        print(f"❌ Test 5 Failed: {e}")
+
+    # 6. Test Seeder Chain
+    print("\n" + "-" * 70)
+    print("Test 6: Seeder Chain (Initial Project Documentation)")
+    print("-" * 70)
+    try:
+        seeder = get_seeder_chain()
+        test_source_code = """
+from flask import Flask, jsonify
+
+app = Flask(__name__)
+
+@app.route('/api/v1/users')
+def get_users():
+    return jsonify({'users': ['Alice', 'Bob']})
+
+if __name__ == '__main__':
+    app.run(debug=True)
+"""
+        seed_docs = seeder.invoke({"source_code": test_source_code})
+        print(f"Response:\n{seed_docs}")
+        assert "Flask" in seed_docs or "API" in seed_docs
+        print("✅ Test 6 Passed!")
+    except Exception as e:
+        print(f"❌ Test 6 Failed: {e}")
+    
+    # Final Summary
+    print("\n" + "=" * 70)
+    print("Self-Test Complete!")
+    print("=" * 70)
+    print("\n💡 All chains are ready to use:")
+    print("   1. Analyzer Chain - Detects functional vs trivial changes")
+    print("   2. Rewriter Chain - Updates existing documentation")
+    print("   3. Creator Chain - Creates new documentation from scratch")
+    print("   4. Summarizer Chain - Generates changelog summaries")
+    print("   5. Seeder Chain - Creates initial project documentation")
+    print("=" * 70)
+
+diff --git a/backend/main.py b/backend/main.py
+index 7fecba5..de3dbe2 100644
+--- a/backend/main.py
+++++ b/backend/main.py
+@@ -197,12 +197,12 @@ async def handle_github_webhook(
+ # --- 3. Root Endpoint (for testing) ---
+ @app.get("/")
+ async def root():
+-    return {"status": "Doc-Ops Agent is running"}
+++    return {"status": "DocSmith is running"}
+ 
+ # --- Run the server (for local testing) ---
+ if __name__ == "__main__":
+     import uvicorn
+-    print("--- Starting Doc-Ops Agent Backend ---")
+++    print("--- Starting DocSmith Backend ---")
+     print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
+     print("--- AI Models are warming up... ---")
+     uvicorn.run(app, host="0.0.0.0", port=8000)
+diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
+index eb531b5..df28c5f 100644
+--- a/frontend/src/App.jsx
+++++ b/frontend/src/App.jsx
+@@ -37,7 +37,7 @@ export default function App() {
+   return (
+     <div className="App">
+       <header className="App-header">
+-        <h1>Autonomous Doc-Ops Agent</h1>
+++        <h1>DocSmith</h1>
+         <div className="header-controls">
+           <StatusBadge status={status} />
+           <DarkModeToggle />
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/USER_GUIDE.md b/backend/USER_GUIDE.md
+index 629049c..6fc069a 100644
+--- a/backend/USER_GUIDE.md
++++ b/backend/USER_GUIDE.md
+@@ -1,10 +1,10 @@
+-# Doc-Ops Agent: User & Setup Guide
++# DocSmith: User & Setup Guide
+ 
+-Welcome to the Doc-Ops Agent! This guide provides all the necessary steps to set up, configure, and run this project. This agent is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
+ 
+ ## 1. Overview
+ 
+-The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
+ 
+ 1.  **Analyzes the code diff** using an AI model (OpenAI).
+ 2.  **Determines if the change is significant** enough to warrant a documentation update.
+@@ -14,7 +14,7 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
+ 
+ ## 2. Core Technologies
+ 
+-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
+ *   **Frontend**: React, Server-Sent Events (SSE) for live logging
+ *   **Vector Store**: FAISS for efficient similarity search
+ 
+@@ -26,7 +26,7 @@ Before you begin, ensure you have the following installed and configured:
+ -   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
+ -   **Git**: [Download Git](https://git-scm.com/downloads/)
+ -   **GitHub Account**: You will need a personal GitHub account.
+-*   **OpenAI API Key**: You need an API key from OpenAI to power the AI analysis. [Get an API Key](https://platform.openai.com/api-keys).
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
+ -   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
+ 
+ ## 4. Setup and Installation
+@@ -84,8 +84,8 @@ The backend is a Python FastAPI application.
+     # Your GitHub Personal Access Token for API actions
+     GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"
+ 
+-    # Your OpenAI API key
+-    OPENAI_API_KEY="sk-YourOpenAIKeyHere"
++    # Your Google AI API key for Gemini
++    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
+ 
+     # (Optional) The minimum confidence score required to update a document
+     CONFIDENCE_THRESHOLD=0.2
+@@ -113,7 +113,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ 1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
+ 2.  Click **Generate new token** (or **Generate new token (classic)**).
+-*   Give it a descriptive name (e.g., "Doc-Ops Agent").
++*   Give it a descriptive name (e.g., "DocSmith").
+  4.  Set the **Expiration** as needed (e.g., 90 days).
+  5.  Select the following **scopes**:
+      *   `repo` (Full control of private repositories)
+@@ -123,7 +123,7 @@ The agent needs this token to create branches and pull requests on your behalf.
+ 
+ This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.
+ 
+-#### OpenAI API Key (`OPENAI_API_KEY`)
++#### Google AI API Key (`GOOGLE_API_KEY`)
+ 
+ 1.  Log in to your OpenAI Platform account.
+ 2.  Go to the **API Keys** section.
+@@ -181,22 +181,22 @@ Now, you need to tell GitHub where to send events. This should be done on the re
+ 
+ ## 8. How to Use the Agent
+ 
+-Your setup is complete! Now you can test the agent's workflow.
++Your setup is complete! Now you can test DocSmith's workflow.
+ 
+ 1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
+ 2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
+ 3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
+ 4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
+-*   **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
++*   **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
+  6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
+ 
+  ---
+ 
+-You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+ 
+ ## 9. Deployment to Render
+ 
+-To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally.
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
+ 
+  1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
+  2.  **Configure the service** with the following settings:
+@@ -208,7 +208,7 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+      *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
+          *   Use the port recommended by Render (e.g., `10000`).
+   3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `OPENAI_API_KEY` that you have in your local `.env` file.
+-*   **Deploy**: Trigger a manual deploy.
++*   **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+   5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+  Your agent is now live and will run automatically in the cloud!
+@@ -211,4 +211,23 @@ To deploy the backend to a persistent cloud service like Render, follow these st
+  4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
+  5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
+ 
+-Your agent is now live and will run automatically in the cloud!
+\ No newline at end of file
++Your agent is now live and will run automatically in the cloud!
++
++## 10. Deployment (Frontend to Vercel)
++
++To deploy the frontend dashboard to a world-class hosting platform like Vercel, follow these steps.
++
++1.  **Sign up for Vercel**: Use your GitHub account to sign up for a free account on [Vercel](https://vercel.com).
++2.  **Import Project**: From your Vercel dashboard, click "Add New..." > "Project" and import your `doc-ops-agent` GitHub repository.
++3.  **Configure Project**:
++    *   Vercel will automatically detect that it's a Create React App.
++    *   Expand the "Root Directory" section and select the `frontend` directory. Vercel will now know to run all build commands from there.
++4.  **Configure Environment Variables**:
++    *   This is the most important step. Expand the "Environment Variables" section.
++    *   Add a new variable with the name `REACT_APP_BACKEND_URL`.
++    *   For the value, paste the public URL of your **backend service** that you deployed on Render (e.g., `https://your-app-name.onrender.com`). **Do not** include a trailing slash or any path.
++5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy your React application, giving you a public URL for your dashboard.
++
++---
++
++You now have a complete, production-ready setup with a backend running on Render and a frontend on Vercel!
+\ No newline at end of file
+diff --git a/backend/data/@Knowledge_base.md b/backend/data/@Knowledge_base.md
+index 28f6635..0e5420a 100644
+--- a/backend/data/@Knowledge_base.md
++++ b/backend/data/@Knowledge_base.md
+@@ -1122,3 +1122,1393 @@ index f422459..4556d9d 100644
+ Binary files a/backend/faiss_index/index.pkl and b/backend/faiss_index/index.pkl differ
+ 
+ ```
++
++
++---
++
++### AI-Generated Update (2025-11-16 15:56:55)
++
++# DocSmith: User & Setup Guide
++
++Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.
++
++## 1. Overview
++
++DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:
++
++1.  **Analyzes the code diff** using an AI model (Google Gemini).
++2.  **Determines if the change is significant** enough to warrant a documentation update.
++3.  **Retrieves relevant existing documentation** snippets from a vector store.
++4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
++5.  **Creates a new pull request** with the documentation changes.
++
++## 2. Core Technologies
++
++*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
++*   **Frontend**: React, Server-Sent Events (SSE) for live logging
++*   **Vector Store**: FAISS for efficient similarity search
++
++## 3. Prerequisites
++
++Before you begin, ensure you have the following installed and configured:
++
++*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
++*   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
++*   **Git**: [Download Git](https://git-scm.com/downloads/)
++*   **GitHub Account**: You will need a personal GitHub account.
++*   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
++*   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).
++
++## 4. Setup and Installation
++
++1.  **Clone the Repository**:
++    ```bash
++    git clone https://github.com/livingcool/doc-ops-agent.git
++    cd doc-ops-agent
++    ```
++
++2.  **Set up Backend Environment**:
++    *   Create a virtual environment:
++        ```bash
++        python -m venv venv
++        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
++        ```
++    *   Install Python dependencies:
++        ```bash
++        pip install -r requirements.txt
++        ```
++    *   Create a `.env` file in the `backend/` directory with your API keys and tokens:
++        ```dotenv
++        # .env file in backend/ directory
++        GITHUB_SECRET_TOKEN="YourGitHubWebhookSecretHere" # From GitHub webhook settings
++        GITHUB_API_TOKEN="ghp_YourGitHubTokenHere" # Your GitHub Personal Access Token
++        GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere" # Your Google AI API Key
++        CONFIDENCE_THRESHOLD=0.2 # Optional: Minimum confidence score for updating docs
++        ```
++
++3.  **Set up Frontend Environment**:
++    *   Navigate to the `frontend/` directory:
++        ```bash
++        cd frontend
++        ```
++    *   Install Node.js dependencies:
++        ```bash
++        npm install
++        ```
++
++4.  **Initialize the Vector Store**:
++    *   Run the Python script to load initial documentation (if any) into the FAISS index:
++        ```bash
++        python ../backend/vector_store.py
++        ```
++        This will create `backend/faiss_index/index.faiss` and `backend/faiss_index/index.pkl`.
++
++## 5. Configuration
++
++### 5.1 GitHub Personal Access Token (`GITHUB_API_TOKEN`)
++
++The agent needs this token to create branches and pull requests on your behalf.
++
++1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
++2.  Click **Generate new token** (or **Generate new token (classic)**).
++3.  Give it a descriptive name (e.g., "DocSmith").
++4.  Set the **Expiration** as needed (e.g., 90 days).
++5.  Select the following **scopes**:
++    *   `repo` (Full control of private repositories)
++    *   `admin:repo_hook` (Full control of repository hooks)
++6.  Click **Generate token** and copy the token immediately. Store it securely in your `.env` file as `GITHUB_API_TOKEN`.
++
++### 5.2 GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)
++
++This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository. Store it in your `.env` file as `GITHUB_SECRET_TOKEN`.
++
++### 5.3 Google AI API Key (`GOOGLE_API_KEY`)
++
++1.  Log in to your Google AI Studio account.
++2.  Go to the **API Key** section.
++3.  Create a new API key or use an existing one.
++4.  Copy the key and store it in your `.env` file as `GOOGLE_API_KEY`.
++
++### 5.4 Confidence Threshold (`CONFIDENCE_THRESHOLD`)
++
++This optional environment variable (defaulting to `0.2`) determines the minimum confidence score required for the agent to *update* existing documentation. If the confidence is lower, or if no relevant documentation is found, the agent will switch to "Create Mode" to generate new documentation.
++
++## 6. Running the Application
++
++1.  **Start the Backend Server**:
++    *   Activate your backend virtual environment (`source venv/bin/activate`).
++    *   Run the FastAPI application:
++        ```bash
++        cd backend
++        uvicorn main:app --reload --port 8000
++        ```
++
++2.  **Start the Frontend Development Server**:
++    *   Open a new terminal.
++    *   Navigate to the `frontend/` directory.
++    *   Run the React development server:
++        ```bash
++        cd frontend
++        npm start
++        ```
++    *   The frontend will be available at `http://localhost:3000`.
++
++3.  **Expose your Local Server with ngrok**:
++    *   Open another terminal.
++    *   Run ngrok to expose your local backend server to the internet:
++        ```bash
++        ngrok http 8000
++        ```
++    *   Copy the `https` forwarding URL provided by ngrok (e.g., `https://your-subdomain.ngrok.io`).
++
++4.  **Configure GitHub Webhook**:
++    *   Go to your GitHub repository's **Settings** > **Webhooks**.
++    *   Click **Add webhook**.
++    *   **Payload URL**: Paste the ngrok `https` URL followed by `/api/webhook/github` (e.g., `https://your-subdomain.ngrok.io/api/webhook/github`).
++    *   **Content type**: Select `application/json`.
++    *   **Secret**: Enter the `GITHUB_SECRET_TOKEN` you defined in your `.env` file.
++    *   **Which events would you like to trigger this webhook?**: Select "Let me select individual events." and choose **Pulls requests** and **Pushes**.
++    *   Ensure **Active** is checked.
++    *   Click **Add webhook**.
++
++## 7. How to Use DocSmith
++
++Your setup is complete! Now you can test DocSmith's workflow.
++
++1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
++2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
++3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
++4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
++5.  **Check for the New PR**: After a minute or two, a new pull request, created by DocSmith, will appear in your repository. This PR will contain the AI-generated documentation updates.
++6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.
++
++---
++
++You are now ready to use DocSmith like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
++
++## 8. Deployment to Render
++
++To deploy the backend to a persistent cloud service like Render, follow these steps. This avoids the need to run `ngrok` locally for a production setup.
++
++1.  **Create a New Web Service** on Render and connect it to your GitHub repository.
++2.  **Configure the service** with the following settings:
++    *   **Build Command**: `pip install -r requirements.txt`
++    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
++        *   Use the port recommended by Render (e.g., `10000`).
++3.  **Add Environment Variables**: Go to the **Environment** tab for your new service and add the same `GITHUB_SECRET_TOKEN`, `GITHUB_API_TOKEN`, and `GOOGLE_API_KEY` that you have in your local `.env` file.
++4.  **Deploy**: Trigger a manual deploy from the Render dashboard to start the service.
++5.  **Update Your Webhook**: Once deployed, Render will provide a public URL (e.g., `https://your-app-name.onrender.com`). Update your GitHub webhook's **Payload URL** to point to this new URL (e.g., `https://your-app-name.onrender.com/api/webhook/github`).
++
++Your agent is now live and will run automatically in the cloud!
++
++---
+
+---
+
+### AI-Generated Update (2025-11-16 14:34:57)
+
+---
+### AI-Generated Update (2025-11-16 13:23:23)
+
+```python
+# --- 3. The "Creator" Chain (NEW) ---
+
+def get_creator_chain():
+    """
+    Returns a chain that creates a NEW documentation section from scratch
+    when no existing documentation is found.
+    """
+    system_prompt = """
+    You are an expert technical writer tasked with creating a new documentation
+    section for a feature that has no prior documentation.
+
+    You will be given:
+    1. A 'git diff' of the new code.
+    2. An AI-generated analysis of what changed.
+```
+
+---
+
+*   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
+*   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
+*   **Create Mode:** If no relevant documentation is found, or if the confidence score for retrieved documents is below the configurable `CONFIDENCE_THRESHOLD`, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
+
+---
+
+### Relevant Code Changes
+```diff
+diff --git a/backend/agent_logic.py b/backend/agent_logic.py
+index 7453050..125ae6b 100644
+--- a/backend/agent_logic.py
++++++ b/backend/agent_logic.py
+@@ -146,6 +146,16 @@ def _append_to_file_sync(file_path: str, content: str):
+     with open(file_path, "a", encoding="utf-8") as f:
+         f.write(content)
+ 
++++def _extract_changed_lines(git_diff: str) -> str:
++++    """A helper to extract only the added/modified lines from a git diff."""
++++    changed_lines = []
++++    for line in git_diff.split('\n'):
++++        # We only care about lines that were added.
++++        if line.startswith('+') and not line.startswith('+++'):
++++            changed_lines.append(line[1:]) # Remove the '+'
++++    
++++    return "\n".join(changed_lines)
++++
 + # --- Updated Core Agent Logic ---
 + 
 + async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
@@ -158,15 +168,21 @@ async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str,
 
     try:
         # --- Step 1: Analyze the code diff ---
++++        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
++++        concise_diff = _extract_changed_lines(git_diff)
++++        if not concise_diff:
++++            await broadcaster("log-skip", "No functional code changes detected in diff.")
++++            return
++++
 +         await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
 -        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
++++        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
         analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
 
         # --- NEW: Generate the clean, human-readable log message ---
         human_readable_summary = await summarizer_chain.ainvoke({
             "user_name": user_name,
             "analysis_summary": analysis_summary,
-            "git_diff": git_diff
+            "git_diff": concise_diff #
