# DocSmith: User & Setup Guide

Welcome to DocSmith! This guide provides all the necessary steps to set up, configure, and run this project. DocSmith is an AI-powered tool that automatically generates documentation for your code changes and creates pull requests with the updates.

## 1. Overview

DocSmith listens for merged pull requests in a GitHub repository. When a PR is merged, it triggers the following workflow:

1.  **Analyzes the code diff** of pushes and merged pull requests using an AI model (Google Gemini).
2.  **Determines if the change is significant** enough to warrant a documentation update.
3.  **Retrieves relevant existing documentation** snippets from a vector store (FAISS).
4.  **Generates new or updated documentation** based on the analysis and retrieved snippets.
5.  **Creates a new pull request** with the documentation changes.

## 2. Core Technologies

*   **Backend**: Python, FastAPI, LangChain, Google Gemini, PyGithub
*   **Frontend**: React, Server-Sent Events (SSE) for live logging
*   **Vector Store**: FAISS for efficient similarity search

## 3. Prerequisites

Before you begin, ensure you have the following installed and configured:

-   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
-   **Node.js and npm**: [Download Node.js](https://nodejs.org/en/download/)
-   **Git**: [Download Git](https://git-scm.com/downloads/)
-   **GitHub Account**: You will need a personal GitHub account.
-   **Google AI API Key**: You need an API key for the Gemini API to power the AI analysis. [Get an API Key](https://ai.google.dev/gemini-api/docs/api-key).
-   **ngrok**: A tool to expose your local server to the internet so GitHub's webhooks can reach it. [Download ngrok](https://ngrok.com/download).

## 4. Setup and Installation

Follow these steps to get the project running on your local machine.

### Step 1: Clone the Repository

First, clone the project repository to your local machine.

```bash
git clone https://github.com/livingcool/doc-ops-agent.git
cd doc-ops-agent
```

### Step 2: Backend Setup

The backend is a Python FastAPI application.

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a Python virtual environment:**
    This isolates the project's dependencies.
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create and configure the `.env` file:**
    Create a file named `.env` in the `backend` directory. This file will store your secret keys and tokens.

    ```
    touch .env
    ```

    Open the `.env` file and add the following variables. See the next section for instructions on how to get these values.

    ```env
    # A secret phrase you create for verifying GitHub webhooks.
    # This MUST EXACTLY match the secret in your GitHub webhook settings.
    GITHUB_SECRET_TOKEN="your_strong_secret_here"

    # Your GitHub Personal Access Token for API actions
    GITHUB_API_TOKEN="ghp_YourGitHubTokenHere"

    # Your Google AI API key for Gemini
    GOOGLE_API_KEY="YourGoogleAIStudioAPIKeyHere"
    ```

### Step 3: Frontend Setup

The frontend is a React application that displays the agent's live logs.

1.  **Open a new terminal** and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

## 5. Acquiring Keys and Tokens

#### GitHub Personal Access Token (`GITHUB_API_TOKEN`)

The agent needs this token to create branches and pull requests on your behalf.

1.  Go to **GitHub Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2.  Click **Generate new token** (or **Generate new token (classic)**).
3.  Give it a descriptive name (e.g., "Doc-Ops Agent").
4.  Set the **Expiration** as needed (e.g., 90 days). For production, consider a fine-grained token.
5.  Select the following **scopes**:
    *   `repo` (Full control of private repositories)
6.  Click **Generate token** and copy the token. **You will not see it again.**

#### GitHub Webhook Secret (`GITHUB_SECRET_TOKEN`)

This is a secret phrase you create. It should be a long, random string. You will use this same secret when setting up the webhook in your GitHub repository.

#### Google AI API Key (`GOOGLE_API_KEY`)

1.  Go to **Google AI Studio**.
2.  Log in and click **"Get API key"** > **"Create API key in new project"**.
3.  Copy the generated key.

## 6. Running the Project

You will need three terminals running simultaneously.

#### Terminal 1: Start the Backend Server

Make sure you are in the `backend` directory with your virtual environment activated.

```bash
uvicorn main:app --reload
```

The backend server will start on `http://127.0.0.1:8000`.

#### Terminal 2: Start the Frontend Application

Make sure you are in the `frontend` directory.

```bash
npm start
```

The React development server will start, and your browser should open to `http://localhost:3000`. You will see a "Live Agent Feed" panel.

#### Terminal 3: Expose Your Local Server with ngrok

GitHub needs a public URL to send webhooks. `ngrok` creates a secure tunnel to your local server.

```bash
ngrok http 8000
```

`ngrok` will give you a public **Forwarding** URL (e.g., `https://random-string.ngrok-free.app`). Copy this HTTPS URL.

## 7. GitHub Webhook Configuration

Now, you need to tell GitHub where to send events. This should be done on the repository you want the agent to watch.

1.  Go to your target GitHub repository's **Settings** > **Webhooks**.
2.  Click **Add webhook**.
3.  **Payload URL**: Paste the `ngrok` HTTPS URL and add `/api/webhook/github` to the end.
    *   Example: `https://<your-ngrok-url>.ngrok-free.app/api/webhook/github`
4.  **Content type**: Select `application/json`.
5.  **Secret**: Paste the same secret you used for `GITHUB_SECRET_TOKEN` in your `.env` file.
6.  **Which events would you like to trigger this webhook?**:
    *   Select **Let me select individual events.**
    *   Ensure both `Pushes` and `Pull requests` are checked.
7.  Ensure **Active** is checked and click **Add webhook**.

## 8. How to Use the Agent

Your setup is complete! Now you can test the agent's workflow.

1.  **Make a Code Change**: In the repository where you set up the webhook, make a change to a file and push it to a new branch.
2.  **Create a Pull Request**: Create a PR to merge your changes into the default branch (e.g., `main`).
3.  **Merge the Pull Request**: Once the PR is merged, GitHub will send a notification to your running agent.
4.  **Observe the Live Feed**: Look at the frontend at `http://localhost:3000`. You will see the agent start its analysis, logging each step in real-time.
5.  **Check for the New PR**: After a minute or two, a new pull request, created by the agent, will appear in your repository. This PR will contain the AI-generated documentation updates.
6.  **Check the Logs**: The `backend/doc_ops_agent.log` file will contain a detailed history of the agent's runs.

## 🧐 Common Mistakes & Troubleshooting

If the agent doesn't behave as expected, check for these common issues:

*   **Gemini API Rate Limits Exceeded**:
    *   **Symptom**: The logs show a `ResourceExhausted: 429` error. This is common on the free tier of the Gemini API, which has a low request-per-minute limit.
    *   **Solution**: Wait a minute for the quota to reset. If this happens frequently, consider upgrading to a paid Google AI plan or adding more robust error handling with exponential backoff in `llm_clients.py`.

*   **GitHub API 409 Conflict Error**:
    *   **Symptom**: The logs show an error like `Failed to update file ... does not match ...: 409`.
    *   **Cause**: This happens when the agent tries to update a file that has been changed since the agent started its process. It's a race condition, often caused by multiple agent runs triggering in quick succession on the same file.
    *   **Solution**: Ensure the agent isn't being triggered multiple times for the same event. The logic to ignore pushes to `ai-docs-fix-*` branches helps, but if you merge PRs very quickly, this can still occur.

*   **Webhook Not Triggering**:
    *   **Symptom**: You merge a PR, but nothing happens in the frontend feed or backend logs.
    *   **Solution**:
        1.  Check that your `ngrok` tunnel is still active and running.
        2.  In your GitHub repo's Webhook settings, go to "Recent Deliveries". Check if the latest event has a green checkmark. If it's a red "X", inspect the response body to see the error message returned from your local server.
        3.  Ensure the Payload URL is correct and that the webhook is subscribed to the right events (`Pull requests`).

---

You are now ready to use the Doc-Ops Agent like a pro! If you encounter any issues, check the terminal output for errors in the backend, frontend, and ngrok consoles.
