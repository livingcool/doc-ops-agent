## Project Giva: AI-Powered Document Q\&A

### 1. Project Overview

Project Giva is a **Python-based RAG (Retrieval-Augmented Generation) system** that allows users to ask questions about their own documents. It uses a **vector database** to store document information and leverages a **Large Language Model (LLM)** to generate human-like answers based on the retrieved context.

The core functionalities include:

### 4. How to Run the Project

#### Prerequisites

Ensure you have Python installed and the required packages from `requirements.txt` (listed below).

You will also need to set up a GitHub Personal Access Token with `repo` scope and set it as an environment variable:

```bash
export GITHUB_API_TOKEN="your_github_token_here"
```

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

--- Snippet 3 (Source: data\README (2).md) ---
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
        
        
## AI Agent Functionality

The AI agent is designed to automatically update documentation based on code changes. When a functional change is detected in a pull request, the agent will:

1.  **Analyze the Code Diff:** Understand the nature and impact of the code changes.
2.  **Gatekeeping:** Determine if the change is functional and requires documentation updates. Trivial changes will be skipped.
3.  **Retrieve Relevant Documentation:** Search the existing documentation for sections related to the code changes.
4.  **Generate New Documentation:** Use an LLM to rewrite or add documentation based on the code analysis and existing context.
5.  **Create GitHub Pull Request:** Automatically create a new branch, commit the updated documentation, and open a pull request against the main branch.

### Agent Workflow

The agent follows these steps:

1.  **Initialization:** AI components (retriever, analyzer, rewriter) are initialized upon application start.
2.  **Analysis:** The `run_agent_analysis` function takes the `git_diff`, `pr_title`, `repo_name`, and `pr_number` as input. It first analyzes the `git_diff` to understand the changes.
3.  **Functional Check:** If the analysis indicates a functional change, the agent proceeds. Otherwise, it skips the process.
4.  **Context Retrieval:** The agent queries the vector store using the analysis summary to find relevant existing documentation snippets.
5.  **Documentation Rewriting:** The LLM is invoked to generate new documentation content based on the code diff and the retrieved context.
6.  **File Identification:** The agent identifies the source files that need updating based on the metadata of the retrieved documents. It ensures paths are correctly formatted (e.g., adding `backend/` prefix and fixing slashes).
7.  **Pull Request Creation:**
    *   Authenticates with GitHub using the `GITHUB_API_TOKEN`.
    *   Creates a new branch based on the default branch (e.g., `main`).
    *   Updates the identified source files with the newly generated content on the new branch.
    *   Opens a pull request with a title and body summarizing the AI-generated changes.
8.  **Logging:** Throughout the process, logs are sent via a `broadcaster` to provide real-time feedback on the agent's progress, including analysis, retrieval, generation, and PR creation status. Errors are also logged.

### Running the Agent (for Development/Testing)

To test the agent logic directly, you can run the `agent_logic.py` file from the `backend` directory. Ensure your `GITHUB_API_TOKEN` is set in your environment.

```bash
# From the 'backend' directory
python agent_logic.py
```

*Note: The self-test section has been removed as the primary execution method is via `uvicorn`.*