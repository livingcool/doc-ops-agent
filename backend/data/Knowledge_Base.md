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
        *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
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

---

## Agent Logic (`agent_logic.py`)

*   **`run_agent_analysis`:** This is the core of the agent.
    *   It first uses an `analyzer_chain` (powered by LangChain) to analyze the provided `git_diff`, determining if it's a functional change and summarizing it.
    *   If it's a functional change, it uses a `retriever` (powered by FAISS and HuggingFace embeddings) to search a vector store of existing documentation for relevant snippets based on the analysis summary.
    *   **Update Mode:** If relevant documentation is found and the confidence score is above a configurable `CONFIDENCE_THRESHOLD` (defaults to 0.2), it uses a `rewriter_chain` to generate updated documentation based on the analysis and the retrieved snippets.
    *   **Create Mode:** If no relevant documentation is found, it uses a `creator_chain` to generate entirely new documentation based on the analysis and the diff.
    *   **Knowledge Base Update:** The newly generated documentation is appended to a central `Knowledge_Base.md` file.

---

# Step 9: Log the final result
        if "Successfully" in result_message:
            # On success, log the specific format you requested.
            log_entry = (
                f"This is an AI-generated documentation update for PR #{pr_number}, "
                f"originally authored by @{user_name}.\n"
                f"Original PR: '{pr_title}' AI Analysis: {analysis_summary}"
            )
            logger.info(log_entry)
        else:
            # On failure, log a simpler error message for clarity.
            logger.error(
                f"AGENT FAILED for PR #{pr_number} ({repo_name}). Reason: {result_message}"
            )

    except Exception as e:
        logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
        await broadcaster("log-error", f"Agent failed with error: {e}")
        return

---

await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")
        
        # --- THIS IS THE CORE LOGIC CHANGE ---
        if not retrieved_docs:
            # --- CREATE MODE ---
            await broadcaster("log-step", "No relevant docs found. Switching to 'Create Mode'...")
            new_documentation = await creator_chain.ainvoke({
                "analysis_summary": analysis_summary,
                "git_diff": git_diff
            })
            # For creation, the source file is always the main knowledge base
            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
        else:
            # --- UPDATE MODE ---
            # Make the confidence threshold configurable for easier testing
            confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
            if confidence_score < confidence_threshold: # Gatekeeping based on confidence
                await broadcaster("log-skip", f"Confidence ({confidence_percent}) is below threshold. Skipping doc update.")
                return

---

def _append_to_file_sync(file_path: str, content: str):
    """Synchronous file append operation."""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)

# --- Updated Core Agent Logic ---

async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
    """This is the main 'brain' of the agent. It runs the full analysis-retrieval-rewrite pipeline."""
    
    if not retriever:
        print("Agent failed: AI components are not initialized.")
        await broadcaster("log-error", "Error: Agent AI components are not ready.")
        return

---

if "Error" in pr_url:
                result_message = f"Failed to create PR. Reason: {pr_url}"
                await broadcaster("log-error", f"Failed to create PR: {pr_url}")
            else:
                result_message = f"Successfully created documentation PR: {pr_url}"
                await broadcaster("log-action", f"✅ Successfully created PR: {pr_url}")

        except Exception as e:
            result_message = f"Agent failed during PR creation with error: {e}"
            await broadcaster("log-error", f"Agent failed with error: {e}")
            # Log the exception traceback for debugging
            logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
        
---
```