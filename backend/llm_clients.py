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
    model="learnlm-2.0-flash-experimental", 
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

# --- 3. The "Creator" Chain (NEW) ---

def get_creator_chain():
    """
    Returns a chain that creates a NEW documentation section from scratch
    when no existing documentation is found.
    """
    system_prompt = """
    You are an expert technical writer tasked with creating a new documentation
    section for a feature that has no prior documentation.

    You will be given:
    1. A 'git diff' of the new code.
    2. An AI-generated analysis of what changed.

    Your job is to write a clear, concise documentation section explaining the new
    feature. The output should be ready to be added to a larger document.
    - Use Markdown formatting.
    - Explain the feature's purpose and how it works based on the code.
    - Do not add commentary like "Here is the new documentation:".
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
        Here is the context for the new feature:
        
        ANALYSIS OF CHANGE:
        {analysis_summary}
        
        CODE CHANGE (GIT DIFF):
        ```diff
        {git_diff}
        ```
        
        Please write a new documentation section for this feature:
        """)
    ])
    
    creator_chain = prompt | llm | StrOutputParser()
    return creator_chain

# --- 4. The "Summarizer" Chain (FOR CLEAN LOGS) ---

def get_summarizer_chain():
    """
    Returns a chain that creates a simple, human-readable summary of a change
    for logging purposes, in the format you requested.
    """
    system_prompt = """
    You are a technical project manager who writes concise, formal changelogs.
    Based on the provided analysis and git diff, produce a single sentence that
    describes the change and its impact.

    The format should be:
    "A push by {user_name} to the file `{file_name}` has {impact_description}."

    - Keep the `impact_description` brief and high-level.
    - Do not include "from this to that".
    - Do not include line numbers.
    - If multiple files are changed, pick the most important one.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
        CONTEXT:
        - User: {user_name}
        - AI Analysis: {analysis_summary}
        - Git Diff:
        ```diff
        {git_diff}
        ```
        Please provide the single-sentence summary for the changelog:
        """)
    ])
    
    summarizer_chain = prompt | llm | StrOutputParser()
    return summarizer_chain

# --- 4. The "Seeder" Chain (NEW) ---

def get_seeder_chain():
    """
    Returns a chain that creates an initial project overview from source code
    to seed the knowledge base.
    """
    system_prompt = """
    You are an expert technical writer tasked with creating a high-level project overview
    to serve as the initial knowledge base for a software project.

    You will be given the concatenated source code of the project's key files.

    Your job is to write a "README" style document that explains:
    1.  What the project is and its main purpose.
    2.  The core technologies used.
    3.  A brief explanation of how the main components (e.g., main.py, agent_logic.py) work together.

    The output should be in Markdown format and serve as a good starting point for project documentation.
    Do not add commentary like "Here is the new documentation:".
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
        Here is the source code of the project:
        
        ```python
        {source_code}
        ```
        
        Please generate the initial project documentation based on this code.
        """)
    ])
    
    seeder_chain = prompt | llm | StrOutputParser()
    return seeder_chain

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
        rewriter = get_rewriter_chain() # <-- Fixed typo
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
        print(f"Test Failed: {e}")