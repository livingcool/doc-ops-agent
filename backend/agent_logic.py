import os
import asyncio
import datetime
import logging
from github import Github
from langchain_core.documents import Document

# --- Import our custom modules ---
from llm_clients import (
    get_analyzer_chain, 
    get_rewriter_chain, 
    format_docs_for_context,
    get_summarizer_chain,
    get_creator_chain
)
from vector_store import get_retriever, add_docs_to_store

# --- Load GitHub Token ---
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# --- Initialize Global "AI" Components ---
try:
    print("Warming up AI components...")
    retriever = get_retriever()
    analyzer_chain = get_analyzer_chain()
    rewriter_chain = get_rewriter_chain()
    creator_chain = get_creator_chain()
    summarizer_chain = get_summarizer_chain()
    print("✅ AI components are ready.")
except Exception as e:
    print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
    retriever, analyzer_chain, rewriter_chain, creator_chain, summarizer_chain = None, None, None, None, None

# --- GitHub PR Creation Logic (Synchronous) ---
def _create_github_pr_sync(logger, repo_name, pr_number, pr_title, pr_body, source_files, new_content):
    """Creates a new branch, updates files, and opens a pull request. (BLOCKING)"""
    # Get a logger instance within the thread to ensure it's configured
    logger = logging.getLogger(__name__)

    if not GITHUB_API_TOKEN:
        return "Error: GITHUB_API_TOKEN not set."

    try:
        # 1. Authenticate and get repo
        g = Github(GITHUB_API_TOKEN)
        repo = g.get_repo(repo_name)
        
        # 2. Get the default branch (e.g., 'main')
        default_branch = repo.get_branch(repo.default_branch)
        
        # 3. Create a new branch name
        new_branch_name = f"ai-docs-fix-pr-{pr_number}"
        
        # 4. Create the new branch from the default branch
        try:
            repo.create_git_ref(
                ref=f"refs/heads/{new_branch_name}",
                sha=default_branch.commit.sha
            )
        except Exception as e:
            if "Reference already exists" in str(e):
                logger.info(f"Branch '{new_branch_name}' already exists. Proceeding...")
            else:
                raise e

        # 5. Update the files
        commit_message = f"docs: AI-generated updates for PR #{pr_number}"
        
        files_updated_count = 0
        for file_path in source_files:
            try:
                # Get the file to get its SHA (required for update)
                contents = repo.get_contents(file_path, ref=default_branch.name)
                
                # Update the file on the *new branch*
                repo.update_file(
                    path=contents.path,
                    message=commit_message,
                    content=new_content, # Using the full AI rewrite
                    sha=contents.sha,
                    branch=new_branch_name
                )
                logger.info(f"Successfully updated file: {file_path}")
                files_updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to update file {file_path}: {e}. Skipping...")

        # 6. Create the Pull Request
        if files_updated_count == 0:
            logger.warning("No files were successfully updated, skipping PR creation.")
            return "Error: No files were updated, so no PR was created."

        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=new_branch_name,
            base=repo.default_branch  # The branch to merge into
        )
        
        print(f"Successfully created PR: {pr.html_url}")
        return pr.html_url

    except Exception as e:
        logger.error(f"Error creating GitHub PR: {e}", exc_info=True)
        return f"Error: {e}"

# --- Async Wrapper for GitHub PR Creation ---
async def create_github_pr_async(*args, **kwargs):
    """
    Runs the synchronous GitHub PR creation function in a separate thread
    to avoid blocking the asyncio event loop.
    """
    # Use asyncio.to_thread which correctly handles passing kwargs to the thread.
    # This is the modern replacement for loop.run_in_executor for this use case.
    pr_url = await asyncio.to_thread(_create_github_pr_sync, *args, **kwargs)
    return pr_url

# --- NEW: Knowledge Base Update Logic ---
async def update_knowledge_base(logger, broadcaster, new_documentation: str):
    """Appends the newly generated documentation to the central knowledge base."""
    knowledge_base_path = os.path.join(os.path.dirname(__file__), 'data', '@Knowledge_base.md')
    
    try:
        await broadcaster("log-step", "Updating central knowledge base...")
        
        # Create a formatted entry with a timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_entry = (
            f"\n\n---\n\n"
            f"### AI-Generated Update ({timestamp})\n\n"
            f"{new_documentation}\n"
        )
        
        # Append to the file asynchronously
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: 
            _append_to_file_sync(knowledge_base_path, update_entry)
        )
        await broadcaster("log-step", "✅ Knowledge base updated.")
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {e}", exc_info=True)
        await broadcaster("log-error", f"Could not update knowledge base: {e}")

def _append_to_file_sync(file_path: str, content: str):
    """Synchronous file append operation."""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)

def _extract_changed_lines(git_diff: str) -> str:
    """A helper to extract only the added/modified lines from a git diff."""
    changed_lines = []
    for line in git_diff.split('\n'):
        # We only care about lines that were added.
        if line.startswith('+') and not line.startswith('+++'):
            changed_lines.append(line[1:]) # Remove the '+'
    
    return "\n".join(changed_lines)

# --- Updated Core Agent Logic ---

async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: str, user_name: str):
    """This is the main 'brain' of the agent. It runs the full analysis-retrieval-rewrite pipeline."""
    
    if not retriever:
        print("Agent failed: AI components are not initialized.")
        await broadcaster("log-error", "Error: Agent AI components are not ready.")
        return

    try:
        # --- Step 1: Analyze the code diff ---
        # --- TOKEN OPTIMIZATION: Analyze only the changed lines ---
        concise_diff = _extract_changed_lines(git_diff)
        if not concise_diff:
            await broadcaster("log-skip", "No functional code changes detected in diff.")
            return

        await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
        analysis = await analyzer_chain.ainvoke({"git_diff": concise_diff})
        analysis_summary = analysis.get('analysis_summary', 'No analysis summary provided.')
        
        # --- NEW: Generate the clean, human-readable log message ---
        human_readable_summary = await summarizer_chain.ainvoke({
            "user_name": user_name,
            "analysis_summary": analysis_summary,
            "git_diff": concise_diff # Use the concise diff here as well
        })
        # Broadcast the clean summary instead of the raw analysis
        await broadcaster("log-summary", human_readable_summary)

        # --- Step 2: Gatekeeping ---
        if not analysis.get('is_functional_change', False):
            await broadcaster("log-skip", "Trivial change detected. No doc update needed.")
            return

        # --- Step 3: Retrieve relevant old docs ---
        await broadcaster("log-step", "Functional change. Searching for relevant docs...")
        # Use `aget_relevant_documents` which returns scores with FAISS
        docs_with_scores = await retriever.vectorstore.asimilarity_search_with_relevance_scores(
            analysis_summary, k=5
        )
        
        retrieved_docs = [doc for doc, score in docs_with_scores]
        scores = [score for doc, score in docs_with_scores]
        
        # Calculate confidence score (highest similarity)
        confidence_score = max(scores) if scores else 0.0
        confidence_percent = f"{confidence_score * 100:.1f}%"

        await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets. Confidence: {confidence_percent}")

        # --- CORE LOGIC CHANGE: Always generate, but decide between "Create" and "Update" ---
        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))
        pr_body_note = ""

        if not retrieved_docs or confidence_score < confidence_threshold:
            # CREATE MODE: No relevant docs found or confidence is too low.
            await broadcaster("log-step", "Low confidence or no docs found. Switching to 'Create Mode'...")
            new_documentation = await creator_chain.ainvoke({
                "analysis_summary": analysis_summary,
                "git_diff": concise_diff # Use the concise diff
            })
            raw_paths = [os.path.join('data', 'Knowledge_Base.md')]
            if confidence_score > 0:
                pr_body_note = f"**⚠️ Low Confidence Warning:** This documentation was generated with a low confidence score of {confidence_percent}. Please review carefully."
        else:
            # UPDATE MODE: High confidence, proceed with rewriting.
            await broadcaster("log-step", "Relevant docs found. Generating updates with LLM...")
            old_docs_context = format_docs_for_context(retrieved_docs)
            new_documentation = await rewriter_chain.ainvoke({
                "analysis_summary": analysis_summary,
                "old_docs_context": old_docs_context,
                "git_diff": git_diff # The rewriter gets the full diff for context
            })
            raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
        
        await broadcaster("log-step", "✅ New documentation generated.")
        
        # --- Step 5: Update the Knowledge Base ---
        # The agent now "remembers" what it wrote by adding it to the central guide.
        await update_knowledge_base(logger, broadcaster, new_documentation)

        # --- Step 6: Incrementally update the vector store (EFFICIENT) ---
        await broadcaster("log-step", "Incrementally updating vector store with new knowledge...")
        new_doc = Document(page_content=new_documentation, metadata={"source": os.path.join('data', 'Knowledge_Base.md')})
        await asyncio.to_thread(add_docs_to_store, [new_doc])
        await broadcaster("log-step", "✅ Knowledge base is now up-to-date.")

        # --- Step 7: Package the results for the PR ---
        
        # --- THIS IS THE FIX: Use the `raw_paths` determined in the Create/Update logic ---
        source_files = []
        for path in raw_paths:
            # 1. Fix Windows slashes
            fixed_path = path.replace("\\", "/") 
            
            # 2. Add the 'backend/' prefix (since docs are in 'backend/data/')
            if not fixed_path.startswith("backend/"):
                fixed_path = f"backend/{fixed_path}"
                
            source_files.append(fixed_path)
        
        print(f"Identified source files to update: {source_files}")

        
        pr_data = {
            "new_content": new_documentation,
            "source_files": source_files,
            "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
            "pr_body": (f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n"
                        f"**Confidence Score:** {confidence_percent}\n\n"
                        f"{pr_body_note}\n\n"
                        f"**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}")
        }

        # --- Step 8: Create the GitHub PR ---
        await broadcaster("log-step", "Attempting to create GitHub pull request...")
        
        try:
            pr_url = await create_github_pr_async(
                repo_name=repo_name,
                logger=logger,
                pr_number=pr_number,
                pr_title=pr_data["pr_title"],
                pr_body=pr_data["pr_body"],
                source_files=pr_data["source_files"],
                new_content=pr_data["new_content"]
            )

            if "Error" in pr_url:
                # Don't broadcast noisy errors to the frontend
                result_message = f"Agent failed during PR creation. Reason: {pr_url}"
            else:
                result_message = f"Successfully created documentation PR: {pr_url}"
                await broadcaster("log-action", f"✅ Successfully created PR: {pr_url}")

        except Exception as e:
            result_message = f"Agent failed during PR creation with error: {e}"
            # Log the exception traceback for debugging
            logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)

        # --- Step 9: Log the final result ---
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
        # Catch all other exceptions and log them without crashing or flooding the UI
        logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
        await broadcaster("log-skip", f"An unexpected error occurred. See server logs for details.")
        return

# --- Self-Test ---
if __name__ == "__main__":
    print("This file is not meant to be run directly.")
    print("Please run 'uvicorn main:app --reload' from the 'backend' directory.")
