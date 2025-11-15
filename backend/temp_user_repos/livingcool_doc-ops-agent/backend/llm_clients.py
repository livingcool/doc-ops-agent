import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

# --- Load API Key ---
load_dotenv()

# Initialize the Generative AI model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest", # <-- FIX: Corrected model name
    temperature=0.2 
)

# --- 1. The "Analyzer" Chain ---

def get_analyzer_chain():
    """
    Returns a chain that analyzes a 'git diff' and outputs JSON.
    """
    
    system_prompt = """
    You are a 'Doc-Ops' code analyzer. Your task is to analyze a 'git diff' 
    and determine if the change is a 'trivial' change (like fixing a typo, 
    adding comments, or refactoring code) or a 'functional' change 
    (like adding a feature, changing an API endpoint, or modifying user-facing behavior).

    You MUST respond in JSON format with two keys:
    1. 'is_functional_change': (boolean) True if the change impacts docs, False otherwise.
    2. 'analysis_summary': (string) A one-sentence summary of the functional change. 
       If 'is_functional_change' is false, this should explain why (e.g., "Refactor, no behavior change.")

    Examples:
    - Diff adding a comment: {{"is_functional_change": false, "analysis_summary": "Trivial change: Added code comments."}}
    - Diff changing an API route: {{"is_functional_change": true, "analysis_summary": "Functional change: Modified the '/api/v1/users' endpoint."}}
    - Diff changing button text: {{"is_functional_change": true, "analysis_summary": "Functional change: Updated user-facing text on the dashboard."}}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Analyze the following git diff:\n\n```diff\n{git_diff}\n```")
    ])
    
    # We pipe the prompt to the LLM and then to a JSON parser
    analyzer_chain = prompt | llm | JsonOutputParser()
    
    return analyzer_chain

# --- 2. The "Rewriter" Chain (UPDATED) ---

def get_rewriter_chain():
    """
    Returns a chain that rewrites documentation.
    """
    
    # --- THIS PROMPT IS UPDATED ---
    system_prompt = """
    You are an expert technical writer. Your task is to rewrite old documentation 
    to match the new code changes.

    You will be given:
    1. The Old Documentation (as a list of relevant snippets).
    2. The 'git diff' of the new code.
    3. An analysis of what changed.

    Your job is to return the new, rewritten documentation.
    - Maintain the original tone and formatting (e.g., Markdown).
    - Do not add commentary like "Here is the new documentation:".
    
    **CRITICAL INSTRUCTION:** After rewriting the documentation, you MUST append
    the relevant code diff. The final output must be in this format:
    
    [Your rewritten documentation text]
    
    ---
    
    ### Relevant Code Changes
    ```diff
    [The exact 'git diff' you were provided]
    ```
    """
    # --- END OF UPDATE ---
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
        Here is the context:
        
        ANALYSIS OF CHANGE:
        {analysis_summary}
        
        OLD DOCUMENTATION SNIPPETS:
        {old_docs_context}
        
        CODE CHANGE (GIT DIFF):
        ```diff
        {git_diff}
        ```
        
        Please provide the new, updated documentation based on these changes:
        """)
    ])
    
    # We pipe this to the LLM and then to a simple string parser
    rewriter_chain = prompt | llm | StrOutputParser()
    
    return rewriter_chain

# --- Helper Function to format docs ---
def format_docs_for_context(docs: list[Document]) -> str:
    """Converts a list of LangChain Documents into a single string."""
    formatted = []
    for i, doc in enumerate(docs):
        snippet = f"--- Snippet {i+1} (Source: {doc.metadata.get('source', 'Unknown')}) ---\n"
        snippet += doc.page_content
        formatted.append(snippet)
    
    if not formatted:
        return "No old documentation snippets were found."
        
    return "\n\n".join(formatted)


# --- Self-Test ---
if __name__ == "__main__":
    
    print("--- Running LLM Clients Self-Test ---")
    
    # 1. Test Analyzer Chain
    print("\n--- Testing Analyzer Chain (Functional Change) ---")
    try:
        analyzer = get_analyzer_chain()
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
        analysis = analyzer.invoke({"git_diff": test_diff_functional})
        print(f"Response:\n{analysis}")
        assert analysis['is_functional_change'] == True
        print("Test Passed.")
    except Exception as e:
        print(f"Test Failed: {e}")
        print("!! Check if your GOOGLE_API_KEY is set in .env !!")

    # 2. Test Analyzer Chain (Trivial Change)
    print("\n--- Testing Analyzer Chain (Trivial Change) ---")
    try:
        analyzer = get_analyzer_chain()
        test_diff_trivial = """
        --- a/api/routes.py
        +++ b/api/routes.py
        @@ -1,3 +1,3 @@
         # This file contains all API routes for our app.
         from flask import Flask, jsonify
         
         # TODO: Add more routes later
        """
        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
        print(f"Response:\n{analysis}")
        assert analysis['is_functional_change'] == False
        print("Test Passed.")
    except Exception as e:
        print(f"Test Failed: {e}")

    # 3. Test Rewriter Chain
    print("\n--- Testing Rewriter Chain ---")
    try:
        rewriter = get_rewriter_chain()
        test_old_docs = [
            Document(page_content="Our API has one user endpoint: /api/v1/users.", metadata={"source": "api.md"})
        ]
        formatted_docs = format_docs_for_context(test_old_docs)
        
        rewrite = rewriter.invoke({
            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
            "old_docs_context": formatted_docs,
            "git_diff": test_diff_functional
        })
        print(f"Response:\n{rewrite}")
        assert "/api/v1/users/profile" in rewrite
        assert "Relevant Code Changes" in rewrite # Test new instruction
        assert "--- a/api/routes.py" in rewrite # Test if diff is included
        print("Test Passed.")
    except Exception as e:
        # --- FIX: Removed the duplicate 'except' block and the misplaced assert statements ---
        print(f"Test Failed: {e}")