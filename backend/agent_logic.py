import asyncio
from langchain_core.documents import Document

# --- Import our custom modules ---
from llm_clients import (
    get_analyzer_chain, 
    get_rewriter_chain, 
    format_docs_for_context
)
from vector_store import get_retriever

# --- Initialize Global "AI" Components ---
# We initialize these once when the app starts
# This is a hackathon-friendly way to "warm up" the models
try:
    print("Warming up AI components...")
    retriever = get_retriever()
    analyzer_chain = get_analyzer_chain()
    rewriter_chain = get_rewriter_chain()
    print("✅ AI components are ready.")
except Exception as e:
    print(f"🔥 FATAL ERROR: Failed to initialize AI components: {e}")
    print("Please check your .env file, API keys, and model installations.")
    retriever, analyzer_chain, rewriter_chain = None, None, None


# --- The Core Agent Logic ---

async def run_agent_analysis(broadcaster, git_diff: str, pr_title: str):
    """
    This is the main "brain" of the agent. It runs the full
    analysis-retrieval-rewrite pipeline.
    
    It takes a 'broadcaster' object to send live logs to the frontend.
    """
    
    if not retriever:
        print("Agent failed: AI components are not initialized.")
        await broadcaster.push("log-error", "Error: Agent AI components are not ready.")
        return None

    try:
        # --- Step 1: Analyze the code diff ---
        await broadcaster.push("log-step", f"Analyzing diff for PR: '{pr_title}'...")
        
        analysis = await analyzer_chain.ainvoke({"git_diff": git_diff})
        analysis_summary = analysis.get('analysis_summary', 'No summary provided.')
        
        await broadcaster.push("log-step", f"Analysis: {analysis_summary}")

        # --- Step 2: Gatekeeping (Is the change functional?) ---
        if not analysis.get('is_functional_change', False):
            await broadcaster.push("log-skip", "Trivial change detected. No doc update needed. Agent finished.")
            return None # Stop execution
            
        # --- Step 3: Retrieve relevant old docs ---
        await broadcaster.push("log-step", "Functional change detected. Searching for relevant docs...")
        
        # Use the analysis summary as the query for our vector store
        retrieved_docs = await retriever.ainvoke(analysis_summary)
        
        await broadcaster.push("log-step", f"Found {len(retrieved_docs)} relevant doc snippets.")
        
        if not retrieved_docs:
            await broadcaster.push("log-skip", "No relevant docs found to update. Agent finished.")
            return None # Stop execution

        # Format the docs for the LLM prompt
        old_docs_context = format_docs_for_context(retrieved_docs)

        # --- Step 4: Rewrite the docs ---
        await broadcaster.push("log-step", "Generating new documentation with LLM...")
        
        new_documentation = await rewriter_chain.ainvoke({
            "analysis_summary": analysis_summary,
            "old_docs_context": old_docs_context,
            "git_diff": git_diff
        })
        
        await broadcaster.push("log-action", "✅ New documentation generated! Ready to create PR.")
        
        # --- Step 5: Return the result ---
        # We also need to return the *source files* to edit
        source_files = list(set([doc.metadata.get('source') for doc in retrieved_docs]))
        
        return {
            "new_content": new_documentation,
            "source_files": source_files, # e.g., ['data/api.md', 'data/tutorial.md']
            "pr_title": f"docs: Update docs for '{pr_title}'",
            "pr_body": f"AI-generated doc update based on code changes in '{pr_title}'.\n\n**Analysis:** {analysis_summary}"
        }

    except Exception as e:
        print(f"🔥 AGENT ERROR: {e}")
        await broadcaster.push("log-error", f"Agent failed with error: {e}")
        return None


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