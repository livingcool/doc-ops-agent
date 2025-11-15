import json
import os
import shutil
import git
import time # Import time for retries
import stat # Import stat for file permissions
from cryptography.fernet import Fernet
from contextlib import contextmanager

# --- File Paths ---
USERS_FILE = 'users.json'
LOGS_DIR = 'user_logs'
REPO_CLONE_DIR = 'temp_user_repos'

# --- Encryption ---
ENCRYPTION_KEY_FILE = 'app_secret.key'

def get_encryption_key():
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
    return key

cipher_suite = Fernet(get_encryption_key())

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# --- NEW: Robust rmtree for Windows ---
def force_rmtree(path, max_retries=5):
    """
    Robustly deletes a directory, handling Windows file lock errors.
    """
    for attempt in range(max_retries):
        try:
            # First, try to fix read-only attributes (common in .git)
            for root, dirs, files in os.walk(path):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    os.chmod(full_path, stat.S_IWRITE)
                for dname in dirs:
                    full_path = os.path.join(root, dname)
                    os.chmod(full_path, stat.S_IWRITE)
            
            shutil.rmtree(path)
            print(f"Successfully cleaned up {path}")
            return
        except PermissionError as e:
            print(f"Warning: PermissionError on attempt {attempt+1}/{max_retries}. Retrying in 1s... ({e})")
            time.sleep(1)
        except Exception as e:
            print(f"Error deleting {path}: {e}")
            break # Don't retry on other errors
    print(f"FATAL: Could not delete directory {path} after {max_retries} attempts.")

# --- User Management ---
def get_all_users() -> dict:
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, 'r') as f: return json.load(f)
    except json.JSONDecodeError: return {}

def save_users(users_data: dict):
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def get_user_id_by_repo(repo_full_name: str) -> str | None:
    users = get_all_users()
    for user_id, data in users.items():
        if data.get('repo_full_name') == repo_full_name:
            return user_id
    return None

def get_user_credentials(user_id: str) -> dict | None:
    user_data = get_all_users().get(user_id)
    if not user_data: return None
    try:
        return {
            "user_id": user_id,
            "repo_full_name": user_data.get('repo_full_name'),
            "github_token": decrypt_data(user_data.get('encrypted_github_token')),
            "gemini_key": decrypt_data(user_data.get('encrypted_gemini_key')),
            "model_name": user_data.get('model_name', 'gemini-1.5-pro-latest')
        }
    except Exception as e:
        print(f"Error decrypting keys for user {user_id}: {e}")
        return None

def create_user(repo_full_name: str, github_token: str, gemini_key: str, model_name: str) -> str:
    user_id = repo_full_name.replace('/', '_')
    users = get_all_users()
    users[user_id] = {
        "repo_full_name": repo_full_name,
        "encrypted_github_token": encrypt_data(github_token),
        "encrypted_gemini_key": encrypt_data(gemini_key),
        "model_name": model_name or 'gemini-1.5-pro-latest'
    }
    save_users(users)
    return user_id

# --- UPDATED: User-Specific Logging ---
@contextmanager
def user_logger(user_id: str):
    log_file_path = os.path.join(LOGS_DIR, f"{user_id}.log")
    
    try:
        from main import push_to_global_queue
    except ImportError:
        push_to_global_queue = None

    def log_and_push(event: str, data: str):
        log_message = f"[{event.upper()}] {data}\n"
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"Failed to write to log file {log_file_path}: {e}")
            
        # --- FIX for 'coroutine was never awaited' ---
        if push_to_global_queue:
            import asyncio
            try:
                # Try to get the running loop
                loop = asyncio.get_running_loop()
                loop.create_task(push_to_global_queue(event, data))
            except RuntimeError:
                # If no loop (e.g., in a thread), run in a new one
                asyncio.run(push_to_global_queue(event, data))
        # --- END OF FIX ---

    try:
        yield log_and_push
    except Exception as e:
        log_and_push("log-error", f"An uncaught error occurred: {e}")
        raise e

# --- UPDATED: Onboarding Logic ---
@contextmanager
def clone_repo(repo_full_name: str, github_token: str) -> str | None:
    repo_url = f"https://{github_token}@github.com/{repo_full_name}.git"
    clone_path = os.path.join(REPO_CLONE_DIR, repo_full_name.replace('/', '_'))
    
    if os.path.exists(clone_path):
        force_rmtree(clone_path) # Use our new robust delete
        
    try:
        print(f"Cloning repo {repo_full_name} to {clone_path}...")
        git.Repo.clone_from(repo_url, clone_path, depth=1)
        yield clone_path
    except Exception as e:
        print(f"Failed to clone repo {repo_full_name}: {e}")
        yield None
    finally:
        # Clean up the repo
        if os.path.exists(clone_path):
            force_rmtree(clone_path) # Use our new robust delete