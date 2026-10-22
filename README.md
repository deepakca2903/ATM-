# ATM Account Management Educational Simulator
### Practical Classroom Project | Updated October 2026
**Full-Stack Web Application + Generative AI + Single-Agent & Multi-Agent Agentic AI**

---

> ⚠️ **CRITICAL EDUCATIONAL DISCLAIMER**  
> This software is an **academic educational simulator** designed solely for university coursework and laboratory training.  
> It is **NOT** a real automated teller machine, commercial banking ledger, or electronic funds payment system.  
> **NEVER** use real money, real debit/credit card numbers, or real banking passwords in this software.

---

## 📌 1. Project Overview & Scope

This project transforms a traditional command-line ATM script (`atm.py`) into an enterprise-grade full-stack banking simulator with modern Generative AI and Agentic Multi-Agent collaboration capabilities.

### 🎯 7 Core Banking Scope Items
1. **Create Account**: Register new account (`account_number`, `customer_name`, `balance`, `pin`, `account_type`: *Savings / Current / Checking*).
2. **Check Balance**: Query available funds with timing-safe PBKDF2 PIN verification.
3. **Deposit Money**: Safe funds deposit with automatic transaction ledger recording.
4. **Withdraw Money**: Balance sufficiency validation, limit enforcement, and realistic currency note breakdown dispensing (₹500, ₹200, ₹100).
5. **Change PIN**: Cryptographic update of 4-digit PIN requiring authentication of current PIN and verification matching.
6. **Search Account**: Real-time multi-field search by account number, customer name, or account type.
7. **Close Account**: Permanent account closure strictly enforced **only when balance is exactly ₹0.00**.

---

## 🏗️ 2. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, Modern CSS3 (Glassmorphism, Kiosk CRT/LCD themes), Vanilla JavaScript (Web Audio API for tactile keypad beeps, dynamic receipt generation) |
| **Backend** | Python 3.14, FastAPI, Pydantic v2 validation, Starlette, Uvicorn |
| **Database** | MySQL (Database: `ATM_db`, Table: `Accounts`, `Transactions`), with transparent SQLite fallback |
| **Security** | Salted PBKDF2-HMAC-SHA256 (200,000 iterations, 16-byte random salt, constant-time `hmac.compare_digest`) |
| **Generative AI** | OpenAI-compatible LLM abstraction (compatible with Google Gemini, OpenAI, Groq, Ollama, LM Studio) + Autonomous Heuristic Simulation Engine |
| **Agentic AI** | Single-Agent ReAct Tool Calling + Multi-Agent Triad Committee (Concierge + Fraud Auditor + Financial Advisor) |

---

## 🤖 3. Agentic AI Architecture

### A. Single-Agent Copilot (ReAct Pattern)
- **Role**: *ATM Virtual Teller & Customer Assistant*
- **Available Function Calling Tools**:
  - `search_account_directory(query)`: Live account queries.
  - `preview_withdrawal_capacity(account_number, amount)`: Evaluates fund sufficiency and calculates physical note dispensing breakdown.
  - `explain_atm_policy(topic)`: Explains zero-balance closure, PIN security, transaction limits, and account types.
- **Safety Guardrails**: Never logs, accepts, or outputs raw PINs in the LLM chat context. Redirects sensitive credential operations to the interactive hardware keypad.

### B. Multi-Agent Agentic Committee (Collaborative Triad)
For high-value or sensitive transactions (e.g. withdrawals > ₹25,000, late-night emergency requests, closure requests):
1. **Agent 1: Customer Concierge (Orchestrator)**: Decomposes user intent, structures the transaction proposal, and routes to specialists.
2. **Agent 2: Fraud & Security Risk Auditor**: Analyzes velocity, transaction size-to-balance ratios, anomaly signals, and outputs a risk score (0-100) with a verdict (`APPROVED`, `STEP_UP_AUTH`, `BLOCKED`).
3. **Agent 3: Financial Advisory Specialist**: Assesses liquidity impact, emergency fund preservation, and provides wealth management guidance (e.g., sweep-in savings or fixed deposit recommendations).
4. **Committee Synthesis**: Combines all agent votes into a unified consensus verdict with an audit trail shown in the UI.

---

## 🚀 4. Quickstart Guide

### Step 1: Clone / Navigate to Directory
```bash
cd C:\Users\Lenovo\Desktop\SDP
```

### Step 2: Run the Automated Test Suite
```bash
python test_api.py
```
*Executes all 10 unit and integration tests covering all 7 scope operations, security barriers, and AI endpoints.*

### Step 3: Launch the Full-Stack Application
```bash
python run.py
```
Or directly using Uvicorn:
```bash
uvicorn backend.server:app --reload --port 8000
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 5. Pre-Loaded Demo Credentials

| Account Number | Customer Name | Account Type | PIN | Initial Balance |
| :--- | :--- | :--- | :--- | :--- |
| **123456789** | Dhanu | Savings | **1234** | ₹100,000.00 |

*You can also create new accounts directly from the web interface or via the existing CLI `atm.py`.*

---

## 📂 6. Repository File Layout

```
SDP/
├── backend/
│   ├── __init__.py
│   ├── config.py         # App configuration, DB settings & LLM endpoints
│   ├── database.py       # MySQL connection pool & automatic table initialization
│   ├── models.py         # Pydantic schemas, PBKDF2 hash & verify functions
│   ├── services.py       # 7 Core banking operations + transaction logging
│   ├── agents.py         # Single-Agent tool caller & Multi-Agent committee
│   └── server.py         # FastAPI REST application & static file mounting
├── frontend/
│   ├── index.html        # Interactive Kiosk Terminal, Account Manager, AI Studio
│   ├── style.css         # Modern FinTech UI, tactile keypad & thermal receipt
│   └── app.js            # State machine, keypad audio beeps & API communication
├── test_api.py           # 10 automated test cases (100% pass rate)
├── run.py                # One-click launch script
├── CASE_STUDY.md         # Comprehensive classroom academic case study
└── README.md             # Project documentation
```
