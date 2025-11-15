The core functionalities include:

*   **Document Ingestion:** Loads text files, splits them into chunks, creates embeddings, and stores them in a vector database for efficient searching.
*   **Query Enhancement:** Automatically expands short user queries to improve the relevance of search results.
*   **Conversational Memory:** Remembers the last few questions and answers to provide context-aware responses in an ongoing conversation.
*   **Advanced RAG Pipeline:** Retrieves relevant document chunks, assesses a confidence score, and generates a detailed, well-structured answer.
*   **Source Citing:** Lists the source documents (and pages) that were used to generate the answer, along with a relevance score for each.
*   **Interactive Console:** Provides a user-friendly command-line interface to interact with the system.
*   **Logging:** New functionality has been added to log the output of the system.

### 2. File Structure

The main project logic is contained within the `e:\2025\Project_Learning\RAG\` directory.

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

💡 GIVA ANSWER:

Based on the provided documents, this project is a Retrieval-Augmented Generation (RAG) system designed to answer questions from a local document knowledge base.

Key features include:
*   **AI-Powered Analysis:** It uses an AI assistant named "giva" to provide answers.
*   **Source-Based Answers:** The system relies on context retrieved from documents to formulate its responses.
*   **Conversational Context:** It can maintain a conversation history to provide more coherent answers over multiple questions.

📖 SOURCES (5 documents):

1.  🔥 my\_document\_1.pdf (Page: 2) - Relevance: 0.8123
    Preview: ...The core of the RAG pipeline involves retrieving relevant text chunks from the indexed vector store and feeding them...
2.  📄 another\_doc.txt (Page: 1) - Relevance: 0.6543
    Preview: ...giva is an AI assistant specialized in analyzing and answering questions based on provided documents. Use the following...
...

#### Installation

### New Features: Added /api/v6/error endpoint

added new functionality
logging the output

---
### Relevant Code Changes
```diff
diff --git a/README.md b/README.md
index e7ec8ef..e898a5b 100644
--- a/README.md
+++ b/README.md
@@ -6,4 +6,6 @@
 ### New Features: Added /api/v6/error endpoint
 
 
+added new functionality
+logging the output
 

```