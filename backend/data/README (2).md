### New Features: Added /api/v3/payments endpoint.

1.  **Setup:** Loads environment variables (specifically `GEMINI_API_KEY`) and initializes the `ChatGoogleGenerativeAI` model (`gemini-1.5-flash`).
2.  **Component Initialization:** Creates instances of the core components from the `src` package: `EmbeddingPipeline`, `VectorStore`, and `RAGRetriever`.
3.  **Data Ingestion:**
    * Checks if the vector store is already populated.
    * If not, it loads all documents from the `data/text_files` directory.
    * Uses the `EmbeddingPipeline` to process and embed the documents and adds them to the `VectorStore`.
4.  **Interactive Console Loop:**
    * Starts an infinite `while` loop, prompting the user for a question.
    * Listens for special commands: `exit`/`quit` to terminate and `reset` to clear the conversation history.
    * The user's query is passed to `enhance_query_with_ai`.
    * The (potentially enhanced) query is then passed to `rag_advanced` along with the current conversation history.

* The new question and the start of the AI's answer are appended to the `conversation_history`. The history is trimmed to the last 10 exchanges.
    * The results are displayed in a clean, formatted block.

💡 GIVA ANSWER:

Based on the provided documents, this project is a Retrieval-Augmented Generation (RAG) system designed to answer questions from a local document knowledge base.

Key features include:
*   **AI-Powered Analysis:** It uses an AI assistant named "giva" to provide answers.
*   **Source-Based Answers:** The system relies on context retrieved from documents to formulate its responses.
*   **Conversational Context:** It can maintain a conversation history to provide more coherent answers over multiple questions.

📖 SOURCES (5 documents):

    1.  🔥 my_document_1.pdf (Page: 2) - Relevance: 0.8123
        Preview: ...The core of the RAG pipeline involves retrieving relevant text chunks from the indexed vector store and feeding them...
    2.  📄 another_doc.txt (Page: 1) - Relevance: 0.6543
        Preview: ...giva is an AI assistant specialized in analyzing and answering questions based on provided documents. Use the following...
    ...

#### Installation