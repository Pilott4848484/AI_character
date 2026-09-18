import json
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHATS_DIR = DATA_DIR / "chats"
CONTACTS_FILE = DATA_DIR / "contacts.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "theme": "light",
    "ui_scale": 100,
}


def ensure_dirs():
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_contacts():
    ensure_dirs()
    if not CONTACTS_FILE.exists():
        return []
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contact(name):
    contacts = load_contacts()
    contact = {"id": str(uuid.uuid4()), "name": name}
    contacts.append(contact)
    _write_contacts(contacts)
    return contact


def delete_contact(contact_id):
    contacts = load_contacts()
    contacts = [c for c in contacts if c["id"] != contact_id]
    _write_contacts(contacts)
    path = CHATS_DIR / f"{contact_id}.json"
    if path.exists():
        path.unlink()


def _write_contacts(contacts):
    data = json.dumps(contacts, indent=2, ensure_ascii=False)
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        f.write(data)


def load_messages(contact_id):
    ensure_dirs()
    path = CHATS_DIR / f"{contact_id}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("messages", [])


def delete_chat(contact_id):
    path = CHATS_DIR / f"{contact_id}.json"
    if path.exists():
        path.unlink()


def load_settings():
    ensure_dirs()
    if not SETTINGS_FILE.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)
    merged = dict(DEFAULT_SETTINGS)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    return merged


def save_settings(settings):
    ensure_dirs()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def save_messages(contact_id, messages):
    ensure_dirs()
    path = CHATS_DIR / f"{contact_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"messages": messages}, f, indent=2, ensure_ascii=False)