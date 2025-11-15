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

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("doc_ops_agent.log"),
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
async def handle_github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    raw_body = await request.body()
    
    if not GITHUB_SECRET_TOKEN:
        print("ERROR: GITHUB_SECRET_TOKEN is not set!")
        raise HTTPException(status_code=500, detail="Server configuration error")
        
    if not x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Signature missing")

    hash_object = hmac.new(
        GITHUB_SECRET_TOKEN.encode('utf-8'),
        msg=raw_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        print("ERROR: Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()

    if payload.get("action") == "closed" and payload.get("pull_request", {}).get("merged") == True:
        
        pr_title = payload.get("pull_request", {}).get("title", "Untitled PR")
        repo_name = payload.get("repository", {}).get("full_name")
        pr_number = payload.get("pull_request", {}).get("number")
        user_name = payload.get("pull_request", {}).get("user", {}).get("login", "unknown-user")
        
        # --- START OF THE FIX ---
        # We need the PR's diff_url to fetch the diff
        diff_url = payload.get("pull_request", {}).get("diff_url")
        if not diff_url:
            await push_log("log-error", "Failed to get diff_url from payload.")
            return {"status": "error", "message": "diff_url not found"}
            
        await push_log("log-trigger", f"PR Merged: '{pr_title}'. Agent is starting...")

        # 5. Get the code diff using the GitHub API
        try:
            # We must fetch the diff from the diff_url
            headers = {
                "Authorization": f"token {GITHUB_API_TOKEN}",
                "Accept": "application/vnd.github.v3.diff" # Ask for the diff format
            }
            git_diff_response = requests.get(diff_url, headers=headers)
            git_diff_response.raise_for_status() # Raise error for bad responses
            git_diff = git_diff_response.text
            
            # --- END OF THE FIX ---
            
            # --- 6. Start the Agent (in the background) ---
            asyncio.create_task(
                agent_logic.run_agent_analysis(
                    logger=logger,
                    broadcaster=push_log,
                    git_diff=git_diff,
                    pr_title=pr_title,
                    repo_name=repo_name,
                    pr_number=pr_number,
                    user_name=user_name
                )
            )

        except Exception as e:
            print(f"Error fetching diff: {e}")
            await push_log("log-error", f"Failed to fetch diff from GitHub: {e}")

    return {"status": "ok"}

# --- 3. Root Endpoint (for testing) ---
@app.get("/")
async def root():
    return {"status": "Doc-Ops Agent is running"}

# --- Run the server (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    print("--- Starting Doc-Ops Agent Backend ---")
    print("--- AI Models are warming up... ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)