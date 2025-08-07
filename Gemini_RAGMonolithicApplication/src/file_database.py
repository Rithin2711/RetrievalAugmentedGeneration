import json
import os
from typing import Any, Dict, List, Optional

DATABASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'db')

USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
SESSIONS_FILE = os.path.join(DATABASE_DIR, 'sessions.json')
CHATS_FILE = os.path.join(DATABASE_DIR, 'chats.json')


def _ensure_db_dir():
    os.makedirs(DATABASE_DIR, exist_ok=True)


def _read_json_file(path: str) -> Any:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _write_json_file(path: str, data: Any) -> None:
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


# PUBLIC_INTERFACE
def add_user(user_dict: Dict[str, Any]) -> bool:
    """Adds a new user. Returns True if success, False if user exists."""
    _ensure_db_dir()
    users = _read_json_file(USERS_FILE)
    username = user_dict['username']
    if username in users:
        return False
    users[username] = user_dict
    _write_json_file(USERS_FILE, users)
    return True


# PUBLIC_INTERFACE
def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Gets a user by username. Returns user dict or None if not found."""
    _ensure_db_dir()
    users = _read_json_file(USERS_FILE)
    return users.get(username)


# PUBLIC_INTERFACE
def update_user(username: str, updates: Dict[str, Any]) -> bool:
    """Updates an existing user. Returns True if success, False if not found."""
    _ensure_db_dir()
    users = _read_json_file(USERS_FILE)
    if username not in users:
        return False
    users[username].update(updates)
    _write_json_file(USERS_FILE, users)
    return True


# PUBLIC_INTERFACE
def delete_user(username: str) -> bool:
    """Deletes a user. Returns True if deleted, False if not found."""
    _ensure_db_dir()
    users = _read_json_file(USERS_FILE)
    if username not in users:
        return False
    del users[username]
    _write_json_file(USERS_FILE, users)
    return True


# PUBLIC_INTERFACE
def list_users() -> List[Dict[str, Any]]:
    """Returns list of all user dicts."""
    _ensure_db_dir()
    users = _read_json_file(USERS_FILE)
    return list(users.values())


# -- Sessions CRUD --

# PUBLIC_INTERFACE
def add_session(session_id: str, session_dict: Dict[str, Any]) -> None:
    _ensure_db_dir()
    sessions = _read_json_file(SESSIONS_FILE)
    sessions[session_id] = session_dict
    _write_json_file(SESSIONS_FILE, sessions)


# PUBLIC_INTERFACE
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    _ensure_db_dir()
    sessions = _read_json_file(SESSIONS_FILE)
    return sessions.get(session_id)


# PUBLIC_INTERFACE
def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    _ensure_db_dir()
    sessions = _read_json_file(SESSIONS_FILE)
    if session_id not in sessions:
        return False
    sessions[session_id].update(updates)
    _write_json_file(SESSIONS_FILE, sessions)
    return True


# PUBLIC_INTERFACE
def delete_session(session_id: str) -> bool:
    _ensure_db_dir()
    sessions = _read_json_file(SESSIONS_FILE)
    if session_id not in sessions:
        return False
    del sessions[session_id]
    _write_json_file(SESSIONS_FILE, sessions)
    return True


# PUBLIC_INTERFACE
def list_sessions() -> List[Dict[str, Any]]:
    _ensure_db_dir()
    sessions = _read_json_file(SESSIONS_FILE)
    return list(sessions.values())


# -- Chat History CRUD --

# PUBLIC_INTERFACE
def add_chat(session_id: str, chat: List[Dict[str, Any]]) -> None:
    _ensure_db_dir()
    chats = _read_json_file(CHATS_FILE)
    chats[session_id] = chat
    _write_json_file(CHATS_FILE, chats)


# PUBLIC_INTERFACE
def get_chat(session_id: str) -> Optional[List[Dict[str, Any]]]:
    _ensure_db_dir()
    chats = _read_json_file(CHATS_FILE)
    return chats.get(session_id, [])


# PUBLIC_INTERFACE
def update_chat(session_id: str, chat: List[Dict[str, Any]]) -> bool:
    _ensure_db_dir()
    chats = _read_json_file(CHATS_FILE)
    if session_id not in chats:
        return False
    chats[session_id] = chat
    _write_json_file(CHATS_FILE, chats)
    return True


# PUBLIC_INTERFACE
def delete_chat(session_id: str) -> bool:
    _ensure_db_dir()
    chats = _read_json_file(CHATS_FILE)
    if session_id not in chats:
        return False
    del chats[session_id]
    _write_json_file(CHATS_FILE, chats)
    return True

# PUBLIC_INTERFACE
def list_chats() -> Dict[str, List[Dict[str, Any]]]:
    _ensure_db_dir()
    chats = _read_json_file(CHATS_FILE)
    return chats
