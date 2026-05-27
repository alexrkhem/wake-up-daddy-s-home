import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
PHOTOS_DIR  = BASE_DIR / "photos"
CHROMA_DIR  = BASE_DIR / "chroma_db"
DB_PATH     = DATA_DIR / "dashboard.db"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE       = BASE_DIR / "token.json"

# Permanent file storage (survives app restarts)
if sys.platform.startswith("win"):
    FILES_DIR = Path("C:/Dashboard_Files")
else:
    FILES_DIR = Path.home() / "Dashboard_Files"

for d in [DATA_DIR, UPLOADS_DIR, PHOTOS_DIR, CHROMA_DIR, FILES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY       = os.getenv("ANTHROPIC_API_KEY", "")
NGROK_AUTH_TOKEN        = os.getenv("NGROK_AUTH_TOKEN", "")
GOOGLE_CALENDAR_SCOPES  = ["https://www.googleapis.com/auth/calendar"]
STREAMLIT_PORT          = 8501
