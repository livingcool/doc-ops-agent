import json
import os
import shutil
import git # We'll need the GitPython library
from cryptography.fernet import Fernet
from contextlib import contextmanager

# --- File Paths ---
USERS_FILE = 'users.json'
LOGS_DIR = 'user_logs'
REPO_CLONE_DIR = 'temp_user_repos'

# --- Encryption ---
# A simple key for this hackathon. In a real app, this would be
# a very secure secret. We'll generate one.
ENCRYPTION_KEY_FILE = 'app_secret.key'

def get_encryption_key():
    """Loads or generates a new encryption key."""
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
    """Encrypts a string."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string."""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# --- User Management ---

def get_all_users() -> dict:
    """Loads the users.json file."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users_data: dict):
    """Saves data back to users.json."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def get_user_id_by_repo(repo_full_name: str) -> str | None:
    """Finds a user_id (their repo name) from the full repo name."""
    # The webhook sends 'livingcool/doc-ops-agent'
    # We just want to find a user who registered that repo
    users = get_all_users()
    for user_id, data in users.items():
        if data.get('repo_full_name') == repo_full_name:
            return user_id
    return None

def get_user_credentials(user_id: str) -> dict | None:
    """Gets and decrypts a specific user's credentials."""
    users = get_all_users()
    user_data = users.get(user_id)
    
    if not user_data:
        return None
        
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
    """
    Adds a new user to the database and returns their ID.
    The user_id will just be the repo_full_name (e.g., 'livingcool_doc-ops-agent')
    """
    user_id = repo_full_name.replace('/', '_') # 'livingcool/doc-ops-agent' -> 'livingcool_doc-ops-agent'
    
    users = get_all_users()
    users[user_id] = {
        "repo_full_name": repo_full_name,
        "encrypted_github_token": encrypt_data(github_token),
        "encrypted_gemini_key": encrypt_data(gemini_key),
        "model_name": model_name or 'gemini-1.5-pro-latest'
    }
    save_users(users)
    return user_id

# --- NEW: User-Specific Logging ---

@contextmanager
def user_logger(user_id: str):
    """
    A context manager to safely open and append to a user's log file.
    This also pushes to the *live dashboard* queue.
    """
    log_file_path = os.path.join(LOGS_DIR, f"{user_id}.log")
    
    # We still need a way to push to the live dashboard
    # We'll import main.py's queue for this.
    try:
        from main import push_to_global_queue
    except ImportError:
        # This allows the file to be imported without circular dependency
        print("Could not import global log queue. Live dashboard will not update.")
        push_to_global_queue = None

    def log_and_push(event: str, data: str):
        log_message = f"[{event.upper()}] {data}\n"
        
        # 1. Write to the user's private log file
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"Failed to write to log file {log_file_path}: {e}")
            
        # 2. Push to the live dashboard (if available)
        if push_to_global_queue:
            # We don't await this, just fire-and-forget
            import asyncio
            asyncio.create_task(push_to_global_queue(event, data))

    try:
        yield log_and_push
    except Exception as e:
        log_and_push("log-error", f"An uncaught error occurred: {e}")
        raise e

# --- NEW: Onboarding Logic (Cloning and Indexing) ---
@contextmanager
def clone_repo(repo_full_name: str, github_token: str) -> str | None:
    """
    Clones a user's repo into a temp folder and yields the path.
    Deletes the folder on exit.
    """
    repo_url = f"https://{github_token}@github.com/{repo_full_name}.git"
    clone_path = os.path.join(REPO_CLONE_DIR, repo_full_name.replace('/', '_'))
    
    # Clean up old clone if it exists
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)
        
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
            shutil.rmtree(clone_path)
            print(f"Cleaned up {clone_path}.")