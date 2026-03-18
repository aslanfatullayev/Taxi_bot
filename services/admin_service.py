"""
Admin service for handling pending driver registrations.
We use an in-memory dictionary for simplicity, but in production, 
this could be a "pending_drivers" database table.
"""

# Format: user_id -> {"name": ..., "phone": ..., "car_model": ..., "car_number": ...}
PENDING_DRIVERS: dict[int, dict] = {}


def add_pending_driver(user_id: int, data: dict) -> None:
    """Store driver data temporarily for admin approval."""
    PENDING_DRIVERS[user_id] = data


def get_pending_driver(user_id: int) -> dict | None:
    """Retrieve pending driver data."""
    return PENDING_DRIVERS.get(user_id)


def remove_pending_driver(user_id: int) -> None:
    """Remove pending driver data after approval or rejection."""
    PENDING_DRIVERS.pop(user_id, None)


# ── Admin Auth System ──────────────────────────────────────────────────────
import os

CODE_FILE = "admin_code.txt"
DEFAULT_CODE = "1234"
SECONDARY_ADMINS: set[int] = set()

def get_admin_code() -> str:
    """Read the current admin access code from file or return default."""
    if os.path.exists(CODE_FILE):
        with open(CODE_FILE, "r") as f:
            return f.read().strip()
    return DEFAULT_CODE

def set_admin_code(new_code: str) -> None:
    """Set and save a new admin access code."""
    with open(CODE_FILE, "w") as f:
        f.write(new_code.strip())

