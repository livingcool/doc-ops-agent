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