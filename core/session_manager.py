import json
import os
import uuid
from datetime import datetime

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def save_session(session_id, chat_history):
    """Saves or updates a chat session to a JSON file."""
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    file_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    # Get a title from the first message or use timestamp
    title = chat_history[0][0][:20] + "..." if chat_history else "New Session"
    
    data = {
        "session_id": session_id,
        "title": title,
        "updated_at": datetime.now().isoformat(),
        "history": chat_history
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return session_id

def list_sessions():
    """Returns a list of all sessions sorted by date."""
    sessions = []
    for f in os.listdir(SESSION_DIR):
        if f.endswith(".json"):
            with open(os.path.join(SESSION_DIR, f), "r", encoding="utf-8") as file:
                data = json.load(file)
                sessions.append({"id": data["session_id"], "title": data["title"], "time": data["updated_at"]})
    return sorted(sessions, key=lambda x: x["time"], reverse=True)

def load_session(session_id):
    """Loads a specific session's history."""
    file_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)["history"]
    return []