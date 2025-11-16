# Doc-Ops Agent: AI-Powered Documentation Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Doc-Ops Agent is an intelligent system designed to automate the creation and maintenance of software documentation. It monitors GitHub pull requests, analyzes code changes, and uses Large Language Models (LLMs) to generate or update documentation, finally submitting the changes as a new pull request.

The agent is built with a self-improving knowledge base, ensuring that as your codebase evolves, your documentation stays perfectly in sync.

## ✨ Features

*   **Automated PR Analysis**: Analyzes the `git diff` of incoming pull requests to identify functional code changes.
*   **Intelligent Doc Generation**: Determines whether to create new documentation or update existing articles based on a confidence score from a vector search.
*   **Self-Improving Knowledge Base**: New documentation is added back to a central knowledge base and vector store, making the agent smarter over time.
*   **GitHub Integration**: Automatically creates a new branch and pull request with the suggested documentation changes.
*   **Real-time Frontend**: A web interface to trigger the agent and view real-time logs of its analysis and actions.
*   **Dual-Mode Operation**:
    *   **Create Mode**: Generates new documentation from scratch when no relevant existing docs are found.
    *   **Update Mode**: Rewrites and refines existing documentation using the code changes as context.

## 🛠️ Tech Stack

*   **Backend**:
    *   **Framework**: FastAPI
    *   **AI/LLM Orchestration**: LangChain
    *   **Vector Store**: FAISS for efficient similarity search.
    *   **GitHub API**: PyGithub to interact with repositories.
    *   **Server**: Uvicorn for local development.
*   **Frontend**:
    *   JavaScript framework (e.g., React, Next.js, Vue)
    *   WebSocket client for real-time log streaming.
*   **Deployment**:
    *   Vercel for both frontend hosting and backend serverless functions.

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.9+
*   Node.js and npm
*   A GitHub account and a Personal Access Token with `repo` scope.
*   An OpenAI API Key (or another LLM provider key compatible with LangChain).

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd doc-ops-agent
```

### 2. Backend Setup

Navigate to the backend directory and set up the Python environment.

```bash
# Go to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Create an environment file
touch .env
```

Add the following environment variables to the `.env` file. These are crucial for the agent to function.

```env
# .env

# Your GitHub Personal Access Token with repo scope
GITHUB_API_TOKEN="ghp_..."

# Your OpenAI API key
OPENAI_API_KEY="sk-..."

# Threshold for deciding between "Create" and "Update" mode (0.0 to 1.0)
# A lower value makes the agent more likely to "Update" existing docs.
CONFIDENCE_THRESHOLD="0.2"
```

### 3. Frontend Setup

Navigate to the frontend directory to install the Node.js dependencies.

```bash
# From the root directory
cd frontend

# Install dependencies
npm install
```

## 🏃‍♀️ Running Locally

You need to run both the backend and frontend servers simultaneously.

*   **To run the Backend Server:**

    ```bash
    # In the /backend directory
    uvicorn main:app --reload
    ```
    The backend will be available at `http://127.0.0.1:8000`.

*   **To run the Frontend Application:**

    ```bash
    # In the /frontend directory
    npm run dev
    ```
    The frontend will be available at `http://localhost:3000` (or another port if specified).

## ☁️ Deployment to Vercel

This project is optimized for deployment on Vercel.

1.  **Push to Git**: Ensure your project is pushed to a GitHub/GitLab/Bitbucket repository.
2.  **Import Project**: In your Vercel dashboard, import the Git repository.
3.  **Configure Project**:
    *   Vercel will automatically detect the frontend framework (like Next.js) and the Python backend via the `vercel.json` file.
    *   Set the **Root Directory** to `frontend`.
4.  **Add Environment Variables**: In the Vercel project settings, add the same environment variables you defined in your `.env` file (`GITHUB_API_TOKEN`, `OPENAI_API_KEY`, `CONFIDENCE_THRESHOLD`).
5.  **Deploy**: Click the "Deploy" button. Vercel will build and deploy both your frontend and your FastAPI backend as a serverless function. Your API will be available at `/api`.

---

This README provides a solid foundation for your project. Feel free to add more specific details about the agent's logic or API endpoints as you continue to build it out.