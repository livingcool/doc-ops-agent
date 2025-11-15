import os
import asyncio
from github import Github
from langchain_core.documents import Document

# --- Import our NEW "factory" functions ---
from llm_clients import (
    get_analyzer_chain, 
    get_rewriter_chain, 
    format_docs_for_context
)
# Import the new user-specific retriever
from vector_store import get_user_retriever

# --- No more global AI components ---

# --- Updated: GitHub PR Creation Logic ---
async def create_github_pr(
    github_token: str, # Now accepts the user's token
    repo_name: str, 
    pr_number: int, 
    pr_title: str, 
    pr_body: str, 
    source_files: list, 
    new_content: str
):
    """
    Creates a new branch, updates files, and opens a pull request
    using the user's specific GitHub token.
    """
    if not github_token:
        return "Error: User's GITHUB_API_TOKEN not found."

    try:
        # 1. Authenticate with the USER'S token
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # 2. Get the default branch (e.g., 'main')
        default_branch = repo.get_branch(repo.default_branch)
        
        # 3. Create a new branch name
        new_branch_name = f"ai-docs-fix-pr-{pr_number}"
        
        # 4. Create the new branch
        try:
            repo.create_git_ref(
                ref=f"refs/heads/{new_branch_name}",
                sha=default_branch.commit.sha
            )
        except Exception as e:
            if "Reference already exists" in str(e):
                print(f"Branch '{new_branch_name}' already exists. Proceeding...")
            else:
                raise e # Propagate other errors

        # 5. Update the files
        commit_message = f"docs: AI-generated updates for PR #{pr_number}"
        files_updated_count = 0
        
        for file_path in source_files:
            try:
                contents = repo.get_contents(file_path, ref=default_branch.name)
                repo.update_file(
                    path=contents.path,
                    message=commit_message,
                    content=new_content,
                    sha=contents.sha,
                    branch=new_branch_name
                )
                print(f"Updated file: {file_path}")
                files_updated_count += 1
            except Exception as e:
                print(f"Failed to update file {file_path}: {e}. Skipping...")

        # 6. Create the Pull Request
        if files_updated_count == 0:
            print("No files were successfully updated, skipping PR creation.")
            return "Error: No files were updated, so no PR was created."

        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=new_branch_name,
            base=repo.default_branch
        )
        
        print(f"Successfully created PR: {pr.html_url}")
        return pr.html_url

    except Exception as e:
        print(f"Error creating GitHub PR: {e}")
        return f"Error: {e}"

# --- UPDATED: Core Agent Logic ---
async def run_agent_analysis(
    user_creds: dict, # User's decrypted credentials
    logger,           # The user-specific logger function
    git_diff: str, 
    pr_title: str, 
    pr_number: int
):
    """
    This is the main "brain" of the agent. It runs the full
    analysis-retrieval-rewrite pipeline for a specific user.
    """
    
    # 1. Get user-specific data from credentials
    user_id = user_creds['user_id']
    gemini_key = user_creds['gemini_key']
    model_name = user_creds['model_name']
    github_token = user_creds['github_token']
    repo_name = user_creds['repo_full_name']

    try:
        # --- Step 1: Get the user's specific "Brain" ---
        await logger("log-step", "Loading user's documentation index...")
        retriever = get_user_retriever(user_id)
        if not retriever:
            await logger("log-error", f"No vector index found for user {user_id}. Did onboarding fail?")
            return

        # --- Step 2: Get the user's specific "Analyzer" LLM ---
        await logger("log-step", f"Analyzing diff for PR: '{pr_title}'...")
        analyzer_chain = get_analyzer_chain(gemini_key, model_name)
        if not analyzer_chain:
            await logger("log-error", f"Failed to create Analyzer LLM for user {user_id}.")
            return
            
        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
        analysis_summary = analysis.get('analysis_summary', 'No summary provided.')
        await logger("log-step", f"Analysis: {analysis_summary}")

        # --- Step 3: Gatekeeping ---
        if not analysis.get('is_functional_change', False):
            await logger("log-skip", "Trivial change detected. No doc update needed.")
            return

        # --- Step 4: Retrieve relevant old docs ---
        await logger("log-step", "Functional change. Searching for relevant docs...")
        retrieved_docs = await retriever.ainvoke(analysis_summary)
        await logger("log-step", f"Found {len(retrieved_docs)} relevant doc snippets.")
        
        if not retrieved_docs:
            await logger("log-skip", "No relevant docs found to update.")
            return

        old_docs_context = format_docs_for_context(retrieved_docs)

        # --- Step 5: Get the user's specific "Rewriter" LLM ---
        await logger("log-step", "Generating new documentation with LLM...")
        rewriter_chain = get_rewriter_chain(gemini_key, model_name)
        if not rewriter_chain:
            await logger("log-error", f"Failed to create Rewriter LLM for user {user_id}.")
            return

        new_documentation = await rewriter_chain.ainvoke({
            "analysis_summary": analysis_summary,
            "old_docs_context": old_docs_context,
            "git_diff": git_diff
        })
        
        await logger("log-step", "✅ New documentation generated.")
        
        # --- Step 6: Package the results (Path Fix) ---
        source_files = []
        for doc in retrieved_docs:
            # We must get the path *relative to the repo root*
            # Our loader saves the full path, e.g., 'temp_user_repos/user_123/docs/api.md'
            # We need to find the "docs/api.md" part
            raw_path = doc.metadata.get('source', '')
            try:
                # Find the path segment after the user_id (which is the repo name)
                # This is a bit of a hack, assumes repo_name is in path
                repo_root_part = user_id.replace('/', '_')
                relative_path = raw_path.split(f"{repo_root_part}/")[1]
                source_files.append(relative_path.replace("\\", "/")) # Fix slashes
            except Exception:
                print(f"Warning: Could not parse relative path from {raw_path}")

        source_files = list(set(source_files)) # Get unique paths
        print(f"Identified source files to update: {source_files}")

        pr_data = {
            "new_content": new_documentation,
            "source_files": source_files,
            "pr_title": f"docs: AI update for '{pr_title}' (PR #{pr_number})",
            "pr_body": f"This is an AI-generated documentation update based on the changes in PR #{pr_number}.\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
        }

        # --- Step 7: Create the GitHub PR ---
        await logger("log-step", "Attempting to create GitHub pull request...")
        
        pr_url = await create_github_pr(
            github_token=github_token, # Use the user's token
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_data["pr_title"],
            pr_body=pr_data["pr_body"],
            source_files=pr_data["source_files"],
            new_content=pr_data["new_content"]
        )

        if "Error" in pr_url:
            await logger("log-error", f"Failed to create PR: {pr_url}")
        else:
            await logger("log-action", f"✅ Successfully created PR: {pr_url}")

    except Exception as e:
        print(f"🔥 AGENT ERROR: {e}")
        await logger("log-error", f"Agent failed with error: {e}")
        return