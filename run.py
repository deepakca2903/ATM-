"""
Launch script for ATM Account Management Educational Simulator
FastAPI Backend + MySQL + HTML/CSS/JS + Single/Multi-Agent AI
"""

import sys
import webbrowser
import time
import uvicorn
from backend.config import settings
from backend.database import db_manager

def main():
    print("=" * 70)
    print("🏦  ATM ACCOUNT MANAGEMENT EDUCATIONAL SIMULATOR (OCTOBER 2026)")
    print("    Full-Stack Web App • MySQL • Generative AI • Multi-Agent AI")
    print("=" * 70)
    print("⚠️  EDUCATIONAL NOTICE: Strictly an educational lab simulator.")
    print("    Never use real monetary currency, real card details, or banking passwords.")
    print("=" * 70)

    # Initialize database
    print("\n[1/3] Initializing database engine...")
    db_manager.init_db()
    print(f"      Active Database: {db_manager.active_db_name}")

    # Launch instructions
    url = f"http://{settings.HOST}:{settings.PORT}"
    print(f"\n[2/3] Web Application UI ready at: {url}")
    print("      Demo Account: #123456789 | PIN: 1234 | Name: Dhanu")
    print("      Interactive ATM Terminal, Account Directory & Agent Studio online.")

    print(f"\n[3/3] Starting FastAPI Server on {url} (Press Ctrl+C to terminate)...")
    
    # Optional auto-open browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("backend.server:app", host=settings.HOST, port=settings.PORT, reload=False)

if __name__ == "__main__":
    main()
