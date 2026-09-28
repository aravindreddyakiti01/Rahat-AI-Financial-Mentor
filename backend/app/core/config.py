import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load environment from backend/.env or root .env
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

DB_PATH = str(DATA_DIR / "rahat.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

APP_TITLE = "RAHAT API"
APP_DESCRIPTION = "Backend API & AI Agent Gateway for Rahat — Personal Financial Mentor for Gig Workers"
APP_VERSION = "1.0.0"
