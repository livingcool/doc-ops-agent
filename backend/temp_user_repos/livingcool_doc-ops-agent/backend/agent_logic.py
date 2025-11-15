import os
import asyncio
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

# --- GitHub PR Creation Logic ---

async def create_github_pr(repo_name, pr_number, pr_title, pr_body, source_files, new_content):
    """
    Creates a new branch, updates files, and opens a pull request.
    """
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
                print(f"Branch '{new_branch_name}' already exists. Proceeding...")
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
            head=new_branch_name,      # The new branch
            base=repo.default_branch  # The branch to merge into
        )
        
        print(f"Successfully created PR: {pr.html_url}")
        return pr.html_url

    except Exception as e:
        print(f"Error creating GitHub PR: {e}")
        return f"Error: {e}"


# --- Updated Core Agent Logic ---

async def run_agent_analysis(broadcaster, git_diff: str, pr_title: str, repo_name: str, pr_number: int):
    """
    This is the main "brain" of the agent. It runs the full
    analysis-retrieval-rewrite pipeline.
    """
    
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
            "pr_body": f"This is an AI-generated documentation update based on the changes in PR #{pr_number}.\n\n**Original PR:** '{pr_title}'\n**AI Analysis:** {analysis_summary}"
        }

        # --- Step 6: Create the GitHub PR ---
        await broadcaster("log-step", "Attempting to create GitHub pull request...")
        
        pr_url = await create_github_pr(
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_data["pr_title"],
            pr_body=pr_data["pr_body"],
            source_files=pr_data["source_files"],
            new_content=pr_data["new_content"]
        )

        if "Error" in pr_url:
            await broadcaster("log-error", f"Failed to create PR: {pr_url}")
        else:
            await broadcaster("log-action", f"✅ Successfully created PR: {pr_url}")

    except Exception as e:
        print(f"🔥 AGENT ERROR: {e}")
        await broadcaster("log-error", f"Agent failed with error: {e}")
        return

# --- Self-Test ---
if __name__ == "__main__":
    """
    This allows you to run this file directly to test it.
    
    1. Make sure your .env file and vector store are working.
    2. Run this command from the 'backend' directory:
       python agent_logic.py
    """
    
    # --- Mock broadcaster for testing ---
    class MockBroadcaster:
        async def push(self, event, data):
            print(f"[LOG-{event.upper()}]: {data}")
    
    mock_broadcaster = MockBroadcaster()

    # --- Test 1: Functional Change ---
    test_diff_functional = """
    --- a/api/routes.py
    +++ b/api/routes.py
    @@ -10,5 +10,6 @@
     @app.route('/api/v1/users')
     def get_users():
         return jsonify(users)
    +
    +@app.route('/api/v1/users/profile')
    +def get_user_profile():
    +    return jsonify({"name": "Test User", "status": "active"})
    """
    
    print("\n--- Running Self-Test (Functional Change) ---")
    
    async def run_test_functional():
        if not retriever:
            print("Skipping test, AI components not loaded.")
            return
            
        result = await run_agent_analysis(
            broadcaster=mock_broadcaster,
            git_diff=test_diff_functional,
            pr_title="feat: Add user profile endpoint"
        )
        if result:
            print("\n--- TEST RESULT ---")
            print(f"PR Title: {result['pr_title']}")
            print(f"Source Files: {result['source_files']}")
            print(f"New Content Snippet: {result['new_content'][:150]}...")
            print("--- Test Passed ---")
        else:
            print("--- Test Failed (Functional) ---")

    # --- Test 2: Trivial Change ---
    test_diff_trivial = """
    --- a/api/routes.py
    +++ b/api/routes.py
    @@ -1,3 +1,3 @@
     # This file contains all API routes for our app.
     from flask import Flask, jsonify
     
     # TODO: Add more routes later
    """
    
    print("\n--- Running Self-Test (Trivial Change) ---")
    
    async def run_test_trivial():
        if not retriever:
            print("Skipping test, AI components not loaded.")
            return
            
        result = await run_agent_analysis(
            broadcaster=mock_broadcaster,
            git_diff=test_diff_trivial,
            pr_title="refactor: Clean up comments"
        )
        if result is None:
            print("--- Test Passed (Correctly skipped) ---")
        else:
            print("--- Test Failed (Should have skipped) ---")

    # Run the async tests
    async def main_test():
        await run_test_functional()
        await run_test_trivial()

    asyncio.run(main_test())