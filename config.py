import os
from dotenv import load_dotenv

load_dotenv()

# Bot token from BotFather
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# List of driver Telegram user IDs
# In production this can be replaced by a database query
DRIVER_IDS: list[int] = [
    int(uid.strip())
    for uid in os.getenv("DRIVER_IDS", "").split(",")
    if uid.strip().isdigit()
]

# Admin IDs for approving drivers
ADMIN_IDS: list[int] = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_IDS", "1517967852").split(",")  # Using your ID as default
    if uid.strip().isdigit()
]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")
