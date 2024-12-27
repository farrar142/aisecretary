import os
from typing import Literal, Union
from returns.result import safe
from dotenv import load_dotenv

load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
SECRETARY_NAMES = os.getenv("SECRETARY_NAMES", "비서").split(",")
DISCORD_WEB_HOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
RECORD_DEVICE = os.getenv("RECORD_DEVICE", None)
CHAT_LIMIT_PER_RECORD: Union[Literal[3], int] = safe(int)(
    os.getenv("CHAT_LIMIT_PER_SECOND", "3")
).unwrap()
CHAT_GPT_MODEL_NAME = os.getenv("CHAT_GPT_MODEL_NAME", "gpt-3.5-turbo")
