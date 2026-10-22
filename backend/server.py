import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import db_manager
from .models import (
    AccountCreateRequest,
    CheckBalanceRequest,
    DepositRequest,
    WithdrawRequest,
    ChangePinRequest,
    CloseAccountRequest,
    SingleAgentChatRequest,
    MultiAgentAnalysisRequest,
    AIConfigUpdateRequest
)
from .services import ATMService
from .agents import SingleAgentCopilot, MultiAgentCommittee, llm_manager

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Educational ATM Banking Simulator with Single-Agent & Multi-Agent Agentic AI (October 2026)"
)

# Enable CORS for educational local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize DB schema
@app.on_event("startup")
def on_startup():
    db_manager.init_db()

# ==========================================
# SYSTEM & HEALTH ENDPOINTS
# ==========================================
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_manager.active_db_name,
        "is_mysql": db_manager.is_mysql,
        "llm_model": llm_manager.model,
        "llm_key_configured": bool(llm_manager.api_key),
        "disclaimer": "⚠️ EDUCATIONAL SIMULATOR ONLY: Not a real ATM, banking ledger, or payment system. Never use real money or credentials."
    }

# ==========================================
# 1. CREATE ACCOUNT
# ==========================================
@app.post("/api/accounts", status_code=201)
def create_account(req: AccountCreateRequest):
    try:
        res = ATMService.create_account(req)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal database error: {str(e)}")

# ==========================================
# 2. CHECK BALANCE
# ==========================================
@app.post("/api/accounts/balance")
def check_balance(req: CheckBalanceRequest):
    try:
        res = ATMService.check_balance(req)
        return res
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# 3. DEPOSIT MONEY
# ==========================================
@app.post("/api/accounts/deposit")
def deposit_money(req: DepositRequest):
    try:
        res = ATMService.deposit(req)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# 4. WITHDRAW MONEY
# ==========================================
@app.post("/api/accounts/withdraw")
def withdraw_money(req: WithdrawRequest):
    try:
        res = ATMService.withdraw(req)
        return res
    except ValueError as e:
        # Use 400 or 401 depending on error message
        status_code = 401 if "PIN" in str(e) or "Authentication" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# 5. CHANGE PIN
# ==========================================
@app.post("/api/accounts/change-pin")
def change_pin(req: ChangePinRequest):
    try:
        res = ATMService.change_pin(req)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# 6. SEARCH ACCOUNT
# ==========================================
@app.get("/api/accounts/search")
def search_accounts(query: Optional[str] = Query(None)):
    try:
        res = ATMService.search_accounts(query)
        return {"count": len(res), "accounts": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/accounts")
def list_all_accounts():
    try:
        res = ATMService.search_accounts("")
        return {"count": len(res), "accounts": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")

# ==========================================
# 7. CLOSE ACCOUNT
# ==========================================
@app.post("/api/accounts/close")
def close_account(req: CloseAccountRequest):
    try:
        res = ATMService.close_account(req)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# TRANSACTION HISTORY
# ==========================================
@app.get("/api/accounts/{account_number}/transactions")
def get_transactions(account_number: int, limit: int = 15):
    try:
        res = ATMService.get_transactions(account_number, limit=limit)
        return {"account_number": account_number, "transactions": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History fetch error: {str(e)}")

# ==========================================
# AI AGENT ENDPOINTS
# ==========================================
@app.post("/api/ai/single-agent")
def single_agent_chat(req: SingleAgentChatRequest):
    try:
        res = SingleAgentCopilot.run(
            message=req.message,
            account_number=req.account_number,
            history=req.history
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.post("/api/ai/multi-agent")
def multi_agent_analysis(req: MultiAgentAnalysisRequest):
    try:
        res = MultiAgentCommittee.run(
            scenario=req.scenario,
            account_number=req.account_number,
            amount=req.amount,
            action_type=req.action_type
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent error: {str(e)}")

@app.get("/api/ai/config")
def get_ai_config():
    return {
        "model": llm_manager.model,
        "base_url": llm_manager.base_url,
        "has_api_key": bool(llm_manager.api_key),
        "api_key_masked": f"{llm_manager.api_key[:4]}...{llm_manager.api_key[-4:]}" if len(llm_manager.api_key) > 8 else ("Configured" if llm_manager.api_key else "Not Configured (Running in Simulation Mode)")
    }

@app.post("/api/ai/config")
def update_ai_config(req: AIConfigUpdateRequest):
    llm_manager.update_config(req.api_key, req.base_url, req.model)
    return {
        "message": "AI configuration updated successfully.",
        "model": llm_manager.model,
        "base_url": llm_manager.base_url,
        "has_api_key": bool(llm_manager.api_key)
    }

# ==========================================
# STATIC FILES & WEB UI
# ==========================================
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_home():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "ATM Backend running. Frontend index.html not found."}
