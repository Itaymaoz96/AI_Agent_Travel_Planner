"""
Load and save user travel preferences to a local .txt file.
"""

from pathlib import Path

from config import USER_PREFERENCES_PATH


def get_preferences_path() -> Path:
    """Return the path to the user preferences file."""
    return Path(USER_PREFERENCES_PATH)


def load_user_preferences() -> str:
    """
    Load user preferences from the local .txt file.
    Returns empty string if the file does not exist or is empty.
    """
    path = get_preferences_path()
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8").strip()
        return content
    except OSError:
        return ""


def save_user_preferences(text: str) -> None:
    """Save user preferences to the local .txt file."""
    path = get_preferences_path()
    path.write_text((text or "").strip(), encoding="utf-8")
