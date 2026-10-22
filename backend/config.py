import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # App Settings
    APP_NAME: str = "ATM Account Management Educational Simulator"
    APP_VERSION: str = "2.5.0 (October 2026)"
    DEBUG: bool = True
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database Configuration (Defaults match the existing classroom MySQL setup)
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql")  # "mysql" or "sqlite"
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "1234")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "ATM_db")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "atm_fallback.db")

    # Security Settings (PBKDF2-HMAC-SHA256 matching atm.py)
    PBKDF2_ITERATIONS: int = 200_000
    MAX_TRANSACTION_LIMIT: float = 100_000.00
    HIGH_RISK_THRESHOLD: float = 25_000.00

    # OpenAI-compatible LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

settings = Settings()
