import json
import os

DB_FILE = "users.json"

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f)

def signup(username, password):
    users = load_users()

    if username in users:
        return False, "User already exists"

    users[username] = {"password": password, "profile": {}}
    save_users(users)

    return True, "Signup successful"

def login(username, password):
    users = load_users()

    if username in users:
        user_data = users[username]
        if isinstance(user_data, str):
            # Legacy format: direct password string comparison
            return user_data == password
        elif isinstance(user_data, dict):
            # Modern format: dict with .get("password")
            return user_data.get("password") == password
        return False
    return False

DATA_DIR = "data"

def get_user(username):
    users = load_users()
    user_data = users.get(username)
    if isinstance(user_data, str):
        # Wrap legacy string as dict for consistency
        return {"password": user_data, "profile": {}}
    return user_data

def update_profile(username, profile_data):
    users = load_users()
    if username in users:
        if not isinstance(users[username], dict):
            users[username] = {"password": users[username], "profile": {}}
        users[username]["profile"] = profile_data
        save_users(users)
        return True
    return False

def load_user_chats(username):
    chat_file = os.path.join(DATA_DIR, f"{username}_aichats.json")
    if not os.path.exists(chat_file):
        return []
    with open(chat_file, "r") as f:
        return json.load(f)

def save_user_chats(username, chats):
    os.makedirs(DATA_DIR, exist_ok=True)
    chat_file = os.path.join(DATA_DIR, f"{username}_aichats.json")
    with open(chat_file, "w") as f:
        json.dump(chats, f, indent=2)
