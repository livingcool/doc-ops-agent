## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, PyGithub, Gemini api
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search
*   **Ddeployment** : Render

---
### Relevant Code Changes
```diff
diff --git a/README.md b/README.md
index d8f9cea..e1ac88c 100644
--- a/README.md
+++ b/README.md
@@ -14,9 +14,10 @@ The Doc-Ops Agent listens for merged pull requests in a GitHub repository. When
 
 ## 2. Core Technologies
 
-*   **Backend**: Python, FastAPI, LangChain, OpenAI, PyGithub
+*   **Backend**: Python, FastAPI, LangChain, PyGithub, Gemini api
 *   **Frontend**: React, Server-Sent Events (SSE) for live logging
 *   **Vector Store**: FAISS for efficient similarity search
+*   **Ddeployment** : Render
 
 ## 3. Prerequisites
 
@@ -190,3 +191,4 @@ Your setup is complete! Now you can test the agent's workflow.
 ---
 
 You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
+
```