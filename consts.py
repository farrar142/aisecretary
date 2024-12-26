import os
from dotenv import load_dotenv

load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
SECRETARY_NAMES = os.getenv("SECRETARY_NAMES", "비서").split(",")
DISCORD_WEB_HOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
RECORD_DEVICE = os.getenv("RECORD_DEVICE", None)
