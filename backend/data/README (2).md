1.  **Setup:** Loads environment variables (specifically `GEMINI_API_KEY`) and initializes the `ChatGoogleGenerativeAI` model (`gemini-2.5-flash-lite`).
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

### 4. How to Run the Project

#### Prerequisites

Ensure you have Python installed and the required packages from `requirements.txt` (listed below).

# Expected Output

--- Starting RAG Pipeline Orchestration ---
✅ LLM initialized (gemini-2.5-flash-lite)

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

| Function | Purpose | Logic |
| :--- | :--- | :--- |
| `enhance_query_with_ai(...)` | To improve document retrieval for short or ambiguous user questions. | If a user's query is less than three words long, it asks the LLM to expand it into a more comprehensive search query, adding synonyms and context. For longer queries, it uses the original query. |
| `rag_simple(...)` | A basic RAG implementation. | Retrieves the top *k* documents, combines their content into a single context, and passes it to the LLM with a straightforward prompt. **Note:** This function is defined but not used in the main execution loop. |

---
### Relevant Code Changes
```diff
diff --git a/backend/llm_clients.py b/backend/llm_clients.py
index 4d9f937..26d852d 100644
--- a/backend/llm_clients.py
+++ b/backend/llm_clients.py
@@ -10,7 +10,7 @@
 
 # Initialize the Generative AI model
 llm = ChatGoogleGenerativeAI(
-    model="gemini-1.5-pro-latest", 
+    model="gemini-2.5-flash-lite", 
     temperature=0.2 
 )
 
```