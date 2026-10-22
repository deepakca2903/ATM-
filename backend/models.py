import hashlib
import hmac
import secrets
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from .config import settings

# ==========================================
# PIN SECURITY HELPERS (PBKDF2-HMAC-SHA256)
# ==========================================
def hash_pin(pin: str) -> str:
    """Store a salted PBKDF2 hash identical to original atm.py."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        bytes.fromhex(salt),
        settings.PBKDF2_ITERATIONS
    ).hex()
    return f"{salt}${hashed}"

def verify_pin(pin: str, stored: str) -> bool:
    """Constant-time comparison of salted PBKDF2 hash."""
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode(),
            bytes.fromhex(salt),
            settings.PBKDF2_ITERATIONS
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

# ==========================================
# CORE ATM REQUEST SCHEMAS
# ==========================================
class AccountCreateRequest(BaseModel):
    account_number: int = Field(..., description="Unique positive integer account number")
    customer_name: str = Field(..., min_length=2, max_length=100, description="Full customer name")
    balance: float = Field(0.0, ge=0.0, description="Initial opening balance (0 or positive)")
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit secret PIN")
    account_type: str = Field(..., description="Savings, Current, or Checking")

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v):
        if v <= 0:
            raise ValueError("Account number must be a positive integer.")
        return v

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("PIN must be exactly 4 numeric digits.")
        return v

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v):
        val = v.strip().capitalize()
        if val not in ("Savings", "Current", "Checking"):
            raise ValueError("Account type must be 'Savings', 'Current', or 'Checking'.")
        return val

class CheckBalanceRequest(BaseModel):
    account_number: int
    pin: str

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("PIN must be 4 digits.")
        return v

class DepositRequest(BaseModel):
    account_number: int
    amount: float = Field(..., gt=0.0, description="Deposit amount must be > 0")

class WithdrawRequest(BaseModel):
    account_number: int
    pin: str
    amount: float = Field(..., gt=0.0, description="Withdrawal amount must be > 0")

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("PIN must be 4 digits.")
        return v

class ChangePinRequest(BaseModel):
    account_number: int
    old_pin: str
    new_pin: str
    confirm_pin: str

    @field_validator("new_pin")
    @classmethod
    def validate_new_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError("New PIN must be exactly 4 digits.")
        return v

class CloseAccountRequest(BaseModel):
    account_number: int
    pin: str
    confirmation: bool = True

# ==========================================
# AI REQUEST & RESPONSE SCHEMAS
# ==========================================
class SingleAgentChatRequest(BaseModel):
    message: str
    account_number: Optional[int] = None
    pin: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

class MultiAgentAnalysisRequest(BaseModel):
    scenario: str
    account_number: int
    amount: Optional[float] = None
    action_type: str = "WITHDRAWAL"

class AIConfigUpdateRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None

# ==========================================
# RESPONSE SCHEMAS
# ==========================================
class AccountResponse(BaseModel):
    account_number: int
    customer_name: str
    balance: float
    account_type: str
    status: str = "Active"

class TransactionResponse(BaseModel):
    id: int
    account_number: int
    transaction_type: str
    amount: float
    balance_after: float
    status: str
    details: Optional[str] = None
    created_at: str
