import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

# --- Load API Key ---
load_dotenv()

# Check if API key exists
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")

# Set the API key for the SDK
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize the Generative AI model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    temperature=0.2 
)

# --- 1. The "Analyzer" Chain ---

def get_analyzer_chain():
    """
    Returns a chain that analyzes a 'git diff' and outputs JSON.
    """
    
    system_prompt = """
You are an analyzer for "DocSmith", an automated documentation agent. Your task is to analyze a 'git diff' 
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

# --- 2. The "Rewriter" Chain ---

def get_rewriter_chain():
    """
    Returns a chain that rewrites documentation.
    """
    
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

# --- 3. The "Creator" Chain ---

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

# --- 4. The "Summarizer" Chain ---

def get_summarizer_chain():
    """
    Returns a chain that creates a simple, human-readable summary of a change
    for logging purposes.
    """
    system_prompt = """
You are a technical project manager who writes concise, formal changelogs.
Based on the provided analysis and git diff, produce a single sentence that
describes the change and its impact.

Your response MUST be a single sentence that follows the format:
"A push by {user_name} to the file `<file_name>` has <impact_description>."

- You must determine the most relevant `<file_name>` from the git diff.
- You must write the `<impact_description>` based on the AI analysis.
- Keep the `impact_description` brief and high-level.
- Do not include "from this to that" or line numbers.
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

# --- 5. The "Seeder" Chain ---

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
1. What the project is and its main purpose.
2. The core technologies used.
3. A brief explanation of how the main components work together.

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
    
    print("=" * 70)
    print("Running Complete Doc-Ops LLM Chains Self-Test")
    print("=" * 70)
    
    # Test data
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
    
    test_diff_trivial = """
--- a/api/routes.py
+++ b/api/routes.py
@@ -1,3 +1,4 @@
 # This file contains all API routes for our app.
 from flask import Flask, jsonify

+# TODO: Add more routes later
"""
    
    # 1. Test Analyzer Chain (Functional Change)
    print("\n" + "-" * 70)
    print("Test 1: Analyzer Chain (Functional Change)")
    print("-" * 70)
    try:
        analyzer = get_analyzer_chain()
        analysis = analyzer.invoke({"git_diff": test_diff_functional})
        print(f"Response:\n{analysis}")
        assert analysis['is_functional_change'] == True
        print("✅ Test 1 Passed!")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        print("⚠️  Check if your GOOGLE_API_KEY is set in .env file!")

    # 2. Test Analyzer Chain (Trivial Change)
    print("\n" + "-" * 70)
    print("Test 2: Analyzer Chain (Trivial Change)")
    print("-" * 70)
    try:
        analyzer = get_analyzer_chain()
        analysis = analyzer.invoke({"git_diff": test_diff_trivial})
        print(f"Response:\n{analysis}")
        assert analysis['is_functional_change'] == False
        print("✅ Test 2 Passed!")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")

    # 3. Test Rewriter Chain
    print("\n" + "-" * 70)
    print("Test 3: Rewriter Chain")
    print("-" * 70)
    try:
        rewriter = get_rewriter_chain()
        test_old_docs = [
            Document(
                page_content="Our API has one user endpoint: /api/v1/users.", 
                metadata={"source": "api.md"}
            )
        ]
        formatted_docs = format_docs_for_context(test_old_docs)
        
        rewrite = rewriter.invoke({
            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
            "old_docs_context": formatted_docs,
            "git_diff": test_diff_functional
        })
        print(f"Response:\n{rewrite}")
        assert "/api/v1/users/profile" in rewrite
        print("✅ Test 3 Passed!")
    except Exception as e:
        print(f"❌ Test 3 Failed: {e}")

    # 4. Test Creator Chain
    print("\n" + "-" * 70)
    print("Test 4: Creator Chain (New Documentation)")
    print("-" * 70)
    try:
        creator = get_creator_chain()
        new_docs = creator.invoke({
            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
            "git_diff": test_diff_functional
        })
        print(f"Response:\n{new_docs}")
        assert "/api/v1/users/profile" in new_docs or "profile" in new_docs.lower()
        print("✅ Test 4 Passed!")
    except Exception as e:
        print(f"❌ Test 4 Failed: {e}")

    # 5. Test Summarizer Chain
    print("\n" + "-" * 70)
    print("Test 5: Summarizer Chain (Changelog)")
    print("-" * 70)
    try:
        summarizer = get_summarizer_chain()
        summary = summarizer.invoke({
            "user_name": "john_doe",
            "analysis_summary": "Functional change: Added new '/api/v1/users/profile' endpoint.",
            "git_diff": test_diff_functional
        })
        print(f"Response:\n{summary}")
        assert "john_doe" in summary or "api/routes.py" in summary
        print("✅ Test 5 Passed!")
    except Exception as e:
        print(f"❌ Test 5 Failed: {e}")

    # 6. Test Seeder Chain
    print("\n" + "-" * 70)
    print("Test 6: Seeder Chain (Initial Project Documentation)")
    print("-" * 70)
    try:
        seeder = get_seeder_chain()
        test_source_code = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/users')
def get_users():
    return jsonify({'users': ['Alice', 'Bob']})

if __name__ == '__main__':
    app.run(debug=True)
"""
        seed_docs = seeder.invoke({"source_code": test_source_code})
        print(f"Response:\n{seed_docs}")
        assert "Flask" in seed_docs or "API" in seed_docs
        print("✅ Test 6 Passed!")
    except Exception as e:
        print(f"❌ Test 6 Failed: {e}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("Self-Test Complete!")
    print("=" * 70)
    print("\n💡 All chains are ready to use:")
    print("   1. Analyzer Chain - Detects functional vs trivial changes")
    print("   2. Rewriter Chain - Updates existing documentation")
    print("   3. Creator Chain - Creates new documentation from scratch")
    print("   4. Summarizer Chain - Generates changelog summaries")
    print("   5. Seeder Chain - Creates initial project documentation")
    print("=" * 70)