import os
import hmac
import hashlib
import asyncio
import logging
import requests # <--- IMPORTED
from dotenv import load_dotenv
from github import Github # PyGithub library
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# --- Import our agent logic ---
import agent_logic 

# --- Load Environment Variables ---
load_dotenv()
GITHUB_SECRET_TOKEN = os.getenv("GITHUB_SECRET_TOKEN")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# --- Define base directory for pathing ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "doc_ops_agent.log")

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler() # To also see logs in the console
    ]
)
logger = logging.getLogger(__name__)

# --- Global App Setup ---
app = FastAPI()
log_queue = asyncio.Queue()

async def push_log(event: str, data: str):
    await log_queue.put({"event": event, "data": data})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check Endpoint ---
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Doc-Ops Agent is healthy"}

# --- 1. The "Live Feed" Endpoint (for React) ---
@app.get("/api/stream/logs")
async def stream_logs(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                print("Client disconnected.")
                break
            message = await log_queue.get()
            yield message
            
    return EventSourceResponse(event_generator())

# --- 2. The "GitHub Webhook" Endpoint (for GitHub) ---
@app.post("/api/webhook/github")
async def handle_github_webhook(
    request: Request, 
    x_github_event: str = Header(None), 
    x_hub_signature_256: str = Header(None)):
    raw_body = await request.body()
    
    if not GITHUB_SECRET_TOKEN:
        print("ERROR: GITHUB_SECRET_TOKEN is not configured on the server.")
        raise HTTPException(status_code=500, detail="Internal server error: Webhook secret not set.")
        
    if not x_hub_signature_256:
        raise HTTPException(status_code=403, detail="X-Hub-Signature-256 header is missing.")

    hash_object = hmac.new(
        GITHUB_SECRET_TOKEN.encode('utf-8'),
        msg=raw_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        print("ERROR: Webhook signature mismatch.")
        raise HTTPException(status_code=403, detail="Invalid webhook signature.")

    payload = await request.json()

    # --- Logic to handle MERGED PULL REQUEST events ---
    if x_github_event == "pull_request" and payload.get("action") == "closed" and payload.get("pull_request", {}).get("merged"):
        pr_title = payload.get("pull_request", {}).get("title", "Untitled PR")
        repo_name = payload.get("repository", {}).get("full_name")
        pr_number = payload.get("pull_request", {}).get("number")
        user_name = payload.get("pull_request", {}).get("user", {}).get("login", "unknown-user")
        diff_url = payload.get("pull_request", {}).get("diff_url")

        if not diff_url:
            await push_log("log-error", "Failed to get diff_url from payload.")
            return {"status": "error", "message": "diff_url not found"}
            
        await push_log("log-trigger", f"PR Merged: '{pr_title}'. Agent is starting...")

        try:
            headers = {
                "Authorization": f"token {GITHUB_API_TOKEN}",
                "Accept": "application/vnd.github.v3.diff"
            }
            git_diff_response = requests.get(diff_url, headers=headers)
            git_diff_response.raise_for_status()
            git_diff = git_diff_response.text
            
            asyncio.create_task(
                agent_logic.run_agent_analysis(
                    logger=logger,
                    broadcaster=push_log,
                    git_diff=git_diff,
                    pr_title=f"PR #{pr_number}: {pr_title}", # Provide more context
                    repo_name=repo_name,
                    pr_number=pr_number,
                    user_name=user_name
                )
            )
        except Exception as e:
            print(f"Error fetching diff: {e}")
            await push_log("log-error", f"Failed to fetch diff from GitHub: {e}")

    # --- NEW: Logic to handle PUSH events ---
    elif x_github_event == "push":
        # Ignore pushes to deleted branches
        if payload.get('deleted'):
            return {"status": "ok", "message": "Ignoring push to deleted branch"}

        repo_name = payload.get("repository", {}).get("full_name")
        pusher_name = payload.get("pusher", {}).get("name", "unknown-user")
        branch = payload.get('ref', 'refs/heads/unknown').split('/')[-1]

        # --- THIS IS THE FIX: Ignore pushes to AI-generated branches to prevent feedback loops ---
        if branch.startswith("ai-docs-fix-pr-"):
            await push_log("log-skip", f"Ignoring push to AI-generated branch '{branch}'.")
            return {"status": "ok", "message": "Event from AI branch ignored."}


        compare_url = payload.get("compare")

        if not compare_url:
            await push_log("log-skip", f"Push by {pusher_name} to {branch} had no changes to compare.")
            return {"status": "ok", "message": "No compare URL, likely a new branch."}

        # The title for a push is the last commit message
        last_commit = payload.get("head_commit")
        if not last_commit:
            await push_log("log-skip", f"Push by {pusher_name} to {branch} had no commits.")
            return {"status": "ok", "message": "No head_commit in push payload."}

        push_title = last_commit.get("message", "Untitled Push")
        # Use the commit ID as the "number" for the agent
        push_id = last_commit.get("id")[:7] 

        await push_log("log-trigger", f"Push to '{branch}' by {pusher_name}. Agent is starting...")

        try:
            # The diff URL for a push is the compare URL with .diff appended
            diff_url = f"{compare_url}.diff"
            headers = {
                "Authorization": f"token {GITHUB_API_TOKEN}",
                "Accept": "application/vnd.github.v3.diff"
            }
            git_diff_response = requests.get(diff_url, headers=headers)
            git_diff_response.raise_for_status()
            git_diff = git_diff_response.text

            # Start the agent analysis in the background
            asyncio.create_task(
                agent_logic.run_agent_analysis(
                    logger=logger,
                    broadcaster=push_log,
                    git_diff=git_diff,
                    pr_title=f"Push to {branch}: {push_title}", # Title for the log
                    repo_name=repo_name,
                    pr_number=push_id, # Use commit hash as a unique identifier
                    user_name=pusher_name
                )
            )
        except Exception as e:
            print(f"Error fetching diff for push: {e}")
            await push_log("log-error", f"Failed to fetch diff from GitHub for push: {e}")

    return {"status": "ok"}

# --- 3. Root Endpoint (for testing) ---
@app.get("/")
async def root():
    return {"status": "Doc-Ops Agent is running"}

# --- Run the server (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    print("--- Starting Doc-Ops Agent Backend ---")
    print("Listening for GitHub webhooks for 'pull_request' (merged) and 'push' events.")
    print("--- AI Models are warming up... ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)