import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    DB_PATH = os.getenv("DB_PATH", "data/cars.db")
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))
    OLX_URL = os.getenv("RECIFE_OLX_URL")