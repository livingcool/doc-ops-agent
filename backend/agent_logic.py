import os
import asyncio
import logging
from github import Github
from langchain_core.documents import Document

# --- Import our custom modules ---
from llm_clients import (
    get_analyzer_chain, 
    get_rewriter_chain, 
    format_docs_for_context
)
from vector_store import get_retriever

# --- Load GitHub Token ---
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# --- Initialize Global "AI" Components ---
try:
    print("Warming up AI components...")
    retriever = get_retriever()
    analyzer_chain = get_analyzer_chain()
    rewriter_chain = get_rewriter_chain()
    print("✅ AI components are ready.")
except Exception as e:
    print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
    retriever, analyzer_chain, rewriter_chain = None, None, None

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

# --- Updated Core Agent Logic ---

async def run_agent_analysis(logger, broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: int, user_name: str):
    """This is the main 'brain' of the agent. It runs the full analysis-retrieval-rewrite pipeline."""
    
    if not retriever:
        print("Agent failed: AI components are not initialized.")
        await broadcaster("log-error", "Error: Agent AI components are not ready.")
        return

    try:
        # --- Step 1: Analyze the code diff ---
        await broadcaster("log-step", f"Analyzing diff for PR: '{pr_title}'...")
        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
        analysis_summary = analysis.get('analysis_summary', 'No summary provided.')
        await broadcaster("log-step", f"Analysis: {analysis_summary}")

        # --- Step 2: Gatekeeping ---
        if not analysis.get('is_functional_change', False):
            await broadcaster("log-skip", "Trivial change detected. No doc update needed.")
            return

        # --- Step 3: Retrieve relevant old docs ---
        await broadcaster("log-step", "Functional change. Searching for relevant docs...")
        retrieved_docs = await retriever.ainvoke(analysis_summary)
        await broadcaster("log-step", f"Found {len(retrieved_docs)} relevant doc snippets.")
        
        if not retrieved_docs:
            await broadcaster("log-skip", "No relevant docs found to update.")
            return

        old_docs_context = format_docs_for_context(retrieved_docs)

        # --- Step 4: Rewrite the docs ---
        await broadcaster("log-step", "Generating new documentation with LLM...")
        new_documentation = await rewriter_chain.ainvoke({
            "analysis_summary": analysis_summary,
            "old_docs_context": old_docs_context,
            "git_diff": git_diff
        })
        
        await broadcaster("log-step", "✅ New documentation generated.")
        
        # --- Step 5: Package the results (THIS IS THE FIX) ---
        
        # Get the raw source paths from metadata
        raw_paths = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
        
        source_files = []
        for path in raw_paths:
            # 1. Fix Windows slashes
            fixed_path = path.replace("\\", "/") 
            
            # 2. Add the 'backend/' prefix (since docs are in 'backend/data/')
            if not fixed_path.startswith("backend/"):
                fixed_path = f"backend/{fixed_path}"
                
            source_files.append(fixed_path)
        
        print(f"Identified source files to update: {source_files}")
        # --- END OF THE FIX ---

        
        pr_data = {
            "new_content": new_documentation,
            "source_files": source_files,
            "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
            "pr_body": f"This is an AI-generated documentation update for PR #{pr_number}, originally authored by **@{user_name}**.\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
        }

        # --- Step 6: Create the GitHub PR ---
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

        # --- Step 7: Create and write the detailed log entry ---
        log_entry = f"""
======================================================================
AGENT RUN FOR PR #{pr_number}
----------------------------------------------------------------------
Repository:          {repo_name}
Author:              @{user_name}
Original PR Title:   '{pr_title}'
AI Analysis:         {analysis_summary}
---
Generated Documentation:
{new_documentation}
---
Result: {result_message}
======================================================================
"""
        logger.info(log_entry)

    except Exception as e:
        logger.error(f"Agent failed for PR #{pr_number} ({repo_name}) with error: {e}", exc_info=True)
        await broadcaster("log-error", f"Agent failed with error: {e}")
        return

# --- Self-Test ---
if __name__ == "__main__":
    print("This file is not meant to be run directly.")
    print("Please run 'uvicorn main:app --reload' from the 'backend' directory.")
