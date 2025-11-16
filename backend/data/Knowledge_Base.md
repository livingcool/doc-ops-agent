# Doc-Ops Agent

This project provides an automated agent that monitors GitHub repositories for code changes. It analyzes these changes, retrieves relevant existing documentation, and either updates the documentation or creates new documentation if none exists. The agent then automatically creates a pull request with the generated documentation updates.

## Purpose

The primary goal of this project is to streamline and improve the documentation process for software projects. By automatically generating and updating documentation based on code changes, it aims to:

*   **Keep documentation up-to-date:** Reduce the burden on developers to manually update documentation, ensuring it accurately reflects the current codebase.
*   **Improve documentation quality:** Leverage AI to generate clear, concise, and contextually relevant documentation.
*   **Enhance discoverability:** Make it easier for team members and contributors to find and understand project information.
*   **Automate repetitive tasks:** Free up developer time by handling the creation and updating of documentation automatically.

## Core Technologies

*   **Python:** The primary programming language for the backend application.
*   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python. It's used here to create the webhook endpoint and the live log stream.
*   **LangChain:** An open-source framework for developing applications powered by language models. It's used for orchestrating the AI's analysis, retrieval, and generation capabilities.
*   **Hugging Face Transformers:** Used for local, efficient embedding generation (`all-MiniLM-L6-v2`).
*   **FAISS:** A library for efficient similarity search and clustering of dense vectors. Used here to store and retrieve documentation embeddings.
*   **GitHub API (PyGithub):** Used to interact with GitHub, specifically for fetching code diffs and creating pull requests.
*   **Requests:** A Python HTTP library, used for making direct API calls to GitHub for diffs.
*   **Uvicorn:** An ASGI server, used to run the FastAPI application.
*   **python-dotenv:** Used to load environment variables from a `.env` file.
*   **SSE-Starlette:** A library for Server-Sent Events, used to stream logs to the frontend in real-time.

## How Components Work Together

The system is designed around a central FastAPI application that listens for GitHub events and orchestrates the AI agent's workflow.

1.  **GitHub Webhook (`/api/webhook/github`):**
    *   This endpoint receives `POST` requests from GitHub.
    *   It verifies the request's authenticity using a shared secret token (`GITHUB_SECRET_TOKEN`) and the `X-Hub-Signature-256` header.
    *   It specifically listens for `pull_request` events (when a PR is `closed` and `merged`) and `push` events.
    *   Upon receiving a relevant event, it extracts the code diff URL from the payload.
    *   It uses the `GITHUB_API_TOKEN` and the `requests` library to fetch the actual code diff content from GitHub.
    *   It then triggers the `agent_logic.run_agent_analysis` function asynchronously, passing the diff content and relevant metadata (like PR title, repo name, etc.).

2.  **Agent Logic (`agent_logic.py`):**
    *   **`run_agent_analysis`:** This is the core of the agent.
        *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
        *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
        *   **Update Mode:** If relevant documentation is found and the confidence score is above a threshold, it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
        *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
        *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.
        *   **Vector Store Re-indexing:** After updating the knowledge base, the `vector_store.create_vector_store()` function is called to rebuild the FAISS index, incorporating the new information. This makes the agent immediately "smarter" for subsequent runs.
        *   **Pull Request Creation:** Finally, it uses the `create_github_pr_async` function to create a new branch, stage the changes, and open a pull request on GitHub with the generated documentation.

3.  **Vector Store (`vector_store.py`):**
    *   **`create_vector_store`:** This function is responsible for building the FAISS index.
        *   It first checks if the `Knowledge_Base.md` is empty and, if so, uses a `seeder_chain` to generate an initial summary of the project's source code to populate it.
        *   It loads all `.md` files from the `data/` directory.
        *   It uses `RecursiveCharacterTextSplitter` to break down the documents into manageable chunks.
        *   It generates embeddings for these chunks using a local `HuggingFaceEmbeddings` model.
        *   It creates a FAISS index from these embeddings and saves it locally to the `faiss_index/` directory.
    *   **`load_vector_store`:** Loads an existing FAISS index from disk.
    *   **`get_retriever`:** This is the primary function used by the agent logic. It attempts to load an existing index; if none is found, it triggers `create_vector_store`. It then returns a LangChain retriever object configured for similarity search with a score threshold.

4.  **Live Logging (`/api/stream/logs`):**
    *   This endpoint uses Server-Sent Events (SSE) to stream log messages from the `log_queue` to any connected client (e.g., a frontend dashboard).
    *   The webhook handler and agent logic push log messages (categorized by event type like `log-step`, `log-error`, `log-action`) into this queue.

5.  **Environment Variables:**
    *   `GITHUB_SECRET_TOKEN`: Used to verify incoming GitHub webhooks.
    *   `GITHUB_API_TOKEN`: Used by the agent to authenticate with the GitHub API for fetching diffs and creating pull requests.

In essence, the system acts as an automated documentation assistant. It watches for code changes, uses AI to understand them and interact with existing knowledge, updates that knowledge, and then proposes the documentation changes back to the project via a pull request.