import os
import hmac
import hashlib
import asyncio
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field

import agent_logic 
import user_manager
import vector_store

load_dotenv()
GITHUB_APP_WEBHOOK_SECRET = os.getenv("GITHUB_SECRET_TOKEN") 

app = FastAPI()

log_queue = asyncio.Queue()

async def push_to_global_queue(event: str, data: str):
    await log_queue.put({"event": event, "data": data})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterRequest(BaseModel):
    repo_full_name: str = Field(..., example="livingcool/doc-ops-agent")
    github_token: str = Field(..., example="ghp_...")
    gemini_key: str = Field(..., example="AIza...")
    model_name: str | None = Field(default="gemini-1.5-pro-latest", example="gemini-1.5-pro-latest")
    docs_folder: str | None = Field(default="docs", example="docs")

def process_new_user(user_id: str, repo_full_name: str, github_token: str, docs_folder: str):
    """
    Background task to clone a repo and build the index.
    This is separate so the API can respond quickly.
    """
    print(f"Starting background indexing for user {user_id}...")
    with user_manager.user_logger(user_id) as logger:
        try:
            # 1. Clone the repo
            with user_manager.clone_repo(repo_full_name, github_token) as clone_path:
                if not clone_path:
                    # --- FIX: Removed asyncio.run() ---
                    logger("log-error", "Failed to clone repo. Check token and repo name.")
                    return

                # 2. Find the docs folder
                docs_path = os.path.join(clone_path, docs_folder)
                if not os.path.exists(docs_path):
                    # --- FIX: Removed asyncio.run() ---
                    logger("log-error", f"Docs folder '{docs_folder}' not found in repo.")
                    return

                # 3. Build the vector store
                logger("log-step", "Cloned repo. Starting to index documentation...")
                success = vector_store.create_user_vector_store(user_id, docs_path)
                
                if success:
                    logger("log-action", "✅ Onboarding complete. Agent is now active.")
                else:
                    logger("log-error", "Failed to build documentation index.")
        except Exception as e:
            # --- FIX: Removed asyncio.run() ---
            logger("log-error", f"Onboarding failed with an unexpected error: {e}")
            
@app.post("/api/register")
async def register_new_user(data: RegisterRequest, background_tasks: BackgroundTasks):
    try:
        user_id = user_manager.create_user(
            repo_full_name=data.repo_full_name,
            github_token=data.github_token,
            gemini_key=data.gemini_key,
            model_name=data.model_name
        )
        
        background_tasks.add_task(
            process_new_user,
            user_id,
            data.repo_full_name,
            data.github_token,
            data.docs_folder
        )
        
        return {"status": "ok", "user_id": user_id, "message": "User registered. Indexing started in background."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register user: {e}")

@app.post("/api/webhook/github")
async def handle_github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    raw_body = await request.body()
    if not GITHUB_APP_WEBHOOK_SECRET:
        print("ERROR: GITHUB_SECRET_TOKEN is not set!")
        raise HTTPException(status_code=500, detail="Server configuration error")
        
    if not x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Signature missing")

    hash_object = hmac.new(GITHUB_APP_WEBHOOK_SECRET.encode('utf-8'), msg=raw_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        print("ERROR: Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()

    if payload.get("action") == "closed" and payload.get("pull_request", {}).get("merged") == True:
        repo_full_name = payload.get("repository", {}).get("full_name")
        user_id = user_manager.get_user_id_by_repo(repo_full_name)
        
        if not user_id:
            print(f"Webhook received for unregistered repo: {repo_full_name}")
            return {"status": "ok", "message": "Repo not registered."}

        creds = user_manager.get_user_credentials(user_id)
        if not creds:
            print(f"Failed to get credentials for user {user_id}")
            return {"status": "error", "message": "Credential error."}

        pr_title = payload.get("pull_request", {}).get("title", "Untitled PR")
        pr_number = payload.get("pull_request", {}).get("number")
        diff_url = payload.get("pull_request", {}).get("diff_url")

        with user_manager.user_logger(user_id) as logger:
            try:
                headers = {
                    "Authorization": f"token {creds['github_token']}",
                    "Accept": "application/vnd.github.v3.diff"
                }
                git_diff_response = requests.get(diff_url, headers=headers)
                git_diff_response.raise_for_status()
                git_diff = git_diff_response.text
                
                asyncio.create_task(
                    agent_logic.run_agent_analysis(
                        user_creds=creds,
                        logger=logger,
                        git_diff=git_diff,
                        pr_title=pr_title,
                        pr_number=pr_number
                    )
                )
            except Exception as e:
                print(f"Error in webhook processing for user {user_id}: {e}")
                asyncio.create_task(logger("log-error", f"Failed to fetch diff or start agent: {e}"))

    return {"status": "ok"}

@app.get("/api/stream/logs")
async def stream_logs(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                print("Dashboard client disconnected.")
                break
            message = await log_queue.get()
            yield message
            
    return EventSourceResponse(event_generator())

@app.get("/")
async def root():
    return {"status": "Doc-Ops Agent (Multi-Tenant) is running"}

if __name__ == "__main__":
    import uvicorn
    os.makedirs(user_manager.LOGS_DIR, exist_ok=True)
    os.makedirs(user_manager.REPO_CLONE_DIR, exist_ok=True)
    os.makedirs(vector_store.BASE_INDEX_PATH, exist_ok=True)
    
    print("--- Starting Doc-Ops Agent Backend (Multi-Tenant) ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)