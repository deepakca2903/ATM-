from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from .database import db_manager
from .models import (
    AccountCreateRequest,
    CheckBalanceRequest,
    DepositRequest,
    WithdrawRequest,
    ChangePinRequest,
    CloseAccountRequest,
    hash_pin,
    verify_pin
)

class ATMService:
    @staticmethod
    def _get_cursor(conn):
        if db_manager.is_mysql:
            return conn.cursor(dictionary=True)
        else:
            return conn.cursor()

    @classmethod
    def get_account_raw(cls, account_number: int, conn) -> Optional[Dict[str, Any]]:
        cursor = cls._get_cursor(conn)
        param_placeholder = "%s" if db_manager.is_mysql else "?"
        query = f"SELECT * FROM Accounts WHERE account_number = {param_placeholder}"
        cursor.execute(query, (account_number,))
        row = cursor.fetchone()
        if not row:
            return None
        if not db_manager.is_mysql:
            return dict(row)
        return row

    @classmethod
    def authenticate(cls, account_number: int, pin: str, conn) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        account = cls.get_account_raw(account_number, conn)
        if not account:
            return False, None, "Account not found."
        
        stored_hash = account.get("pin")
        if not stored_hash or not verify_pin(pin, stored_hash):
            return False, None, "Invalid PIN entered."
        
        return True, account, "Authentication successful."

    @classmethod
    def record_transaction(
        cls,
        conn,
        account_number: int,
        trans_type: str,
        amount: float,
        balance_after: float,
        status: str = "SUCCESS",
        details: str = ""
    ):
        cursor = conn.cursor()
        param = "%s" if db_manager.is_mysql else "?"
        query = f"""
            INSERT INTO Transactions 
            (account_number, transaction_type, amount, balance_after, status, details)
            VALUES ({param}, {param}, {param}, {param}, {param}, {param})
        """
        cursor.execute(query, (account_number, trans_type, amount, balance_after, status, details))

    # ==========================================
    # 1. CREATE ACCOUNT
    # ==========================================
    @classmethod
    def create_account(cls, data: AccountCreateRequest) -> Dict[str, Any]:
        conn = db_manager.get_connection()
        try:
            existing = cls.get_account_raw(data.account_number, conn)
            if existing:
                raise ValueError(f"Account #{data.account_number} already exists.")

            pin_hashed = hash_pin(data.pin)
            cursor = conn.cursor()
            param = "%s" if db_manager.is_mysql else "?"
            
            insert_query = f"""
                INSERT INTO Accounts (account_number, customer_name, balance, pin, account_type)
                VALUES ({param}, {param}, {param}, {param}, {param})
            """
            cursor.execute(insert_query, (
                data.account_number,
                data.customer_name.strip(),
                float(data.balance),
                pin_hashed,
                data.account_type
            ))

            cls.record_transaction(
                conn,
                data.account_number,
                "ACCOUNT_OPENING",
                float(data.balance),
                float(data.balance),
                "SUCCESS",
                f"Initial opening balance deposit ({data.account_type})"
            )

            conn.commit()
            return {
                "account_number": data.account_number,
                "customer_name": data.customer_name,
                "balance": float(data.balance),
                "account_type": data.account_type,
                "message": "Account created successfully."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================
    # 2. CHECK BALANCE
    # ==========================================
    @classmethod
    def check_balance(cls, data: CheckBalanceRequest) -> Dict[str, Any]:
        conn = db_manager.get_connection()
        try:
            ok, account, msg = cls.authenticate(data.account_number, data.pin, conn)
            if not ok:
                raise ValueError(msg)
            
            balance = float(account["balance"])
            return {
                "account_number": account["account_number"],
                "customer_name": account["customer_name"],
                "balance": balance,
                "account_type": account["account_type"]
            }
        finally:
            conn.close()

    # ==========================================
    # 3. DEPOSIT MONEY
    # ==========================================
    @classmethod
    def deposit(cls, data: DepositRequest) -> Dict[str, Any]:
        if data.amount <= 0:
            raise ValueError("Deposit amount must be strictly greater than zero.")
        if data.amount > 10_000_000:
            raise ValueError("Deposit amount exceeds single transaction simulator limit (₹10,000,000).")

        conn = db_manager.get_connection()
        try:
            account = cls.get_account_raw(data.account_number, conn)
            if not account:
                raise ValueError(f"Account #{data.account_number} not found.")

            new_balance = float(account["balance"]) + float(data.amount)
            cursor = conn.cursor()
            param = "%s" if db_manager.is_mysql else "?"
            
            update_query = f"UPDATE Accounts SET balance = balance + {param} WHERE account_number = {param}"
            cursor.execute(update_query, (float(data.amount), data.account_number))

            cls.record_transaction(
                conn,
                data.account_number,
                "DEPOSIT",
                float(data.amount),
                new_balance,
                "SUCCESS",
                f"Deposited ₹{data.amount:,.2f}"
            )

            conn.commit()
            return {
                "account_number": data.account_number,
                "customer_name": account["customer_name"],
                "deposited_amount": float(data.amount),
                "balance": new_balance,
                "message": f"Successfully deposited ₹{data.amount:,.2f}."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================
    # 4. WITHDRAW MONEY
    # ==========================================
    @classmethod
    def calculate_denominations(cls, amount: float) -> Dict[str, int]:
        """Calculates realistic ATM note dispensing breakdown."""
        remaining = int(amount)
        notes = {}
        for denom in [500, 200, 100]:
            count = remaining // denom
            if count > 0:
                notes[f"₹{denom}"] = count
                remaining %= denom
        if remaining > 0:
            notes["Coins/Odd"] = remaining
        return notes

    @classmethod
    def withdraw(cls, data: WithdrawRequest) -> Dict[str, Any]:
        if data.amount <= 0:
            raise ValueError("Withdrawal amount must be strictly greater than zero.")

        conn = db_manager.get_connection()
        try:
            ok, account, msg = cls.authenticate(data.account_number, data.pin, conn)
            if not ok:
                raise ValueError(msg)

            current_balance = float(account["balance"])
            if current_balance < float(data.amount):
                raise ValueError(
                    f"Insufficient funds. Requested: ₹{data.amount:,.2f}, Available: ₹{current_balance:,.2f}."
                )

            new_balance = current_balance - float(data.amount)
            cursor = conn.cursor()
            param = "%s" if db_manager.is_mysql else "?"
            
            update_query = f"""
                UPDATE Accounts 
                SET balance = balance - {param} 
                WHERE account_number = {param} AND balance >= {param}
            """
            cursor.execute(update_query, (float(data.amount), data.account_number, float(data.amount)))

            if cursor.rowcount < 1:
                raise ValueError("Concurrency conflict or insufficient balance during deduction.")

            cls.record_transaction(
                conn,
                data.account_number,
                "WITHDRAWAL",
                float(data.amount),
                new_balance,
                "SUCCESS",
                f"Withdrawn ₹{data.amount:,.2f}"
            )

            conn.commit()
            denominations = cls.calculate_denominations(data.amount)

            return {
                "account_number": data.account_number,
                "customer_name": account["customer_name"],
                "withdrawn_amount": float(data.amount),
                "balance": new_balance,
                "denominations": denominations,
                "message": f"Successfully dispensed ₹{data.amount:,.2f}."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================
    # 5. CHANGE PIN
    # ==========================================
    @classmethod
    def change_pin(cls, data: ChangePinRequest) -> Dict[str, Any]:
        if data.new_pin != data.confirm_pin:
            raise ValueError("New PIN and confirmation PIN do not match.")
        if data.old_pin == data.new_pin:
            raise ValueError("New PIN must be different from the old PIN.")

        conn = db_manager.get_connection()
        try:
            ok, account, msg = cls.authenticate(data.account_number, data.old_pin, conn)
            if not ok:
                raise ValueError(f"Old PIN verification failed: {msg}")

            new_pin_hashed = hash_pin(data.new_pin)
            cursor = conn.cursor()
            param = "%s" if db_manager.is_mysql else "?"
            
            update_query = f"UPDATE Accounts SET pin = {param} WHERE account_number = {param}"
            cursor.execute(update_query, (new_pin_hashed, data.account_number))

            cls.record_transaction(
                conn,
                data.account_number,
                "PIN_CHANGE",
                0.0,
                float(account["balance"]),
                "SUCCESS",
                "PIN successfully updated"
            )

            conn.commit()
            return {
                "account_number": data.account_number,
                "message": "PIN updated successfully. Use your new PIN for future transactions."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================
    # 6. SEARCH ACCOUNT
    # ==========================================
    @classmethod
    def search_accounts(cls, query: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        cursor = cls._get_cursor(conn)
        try:
            param = "%s" if db_manager.is_mysql else "?"
            if not query or not query.strip():
                sql = "SELECT account_number, customer_name, balance, account_type FROM Accounts ORDER BY account_number ASC"
                cursor.execute(sql)
            else:
                q = query.strip()
                sql = f"""
                    SELECT account_number, customer_name, balance, account_type 
                    FROM Accounts 
                    WHERE CAST(account_number AS CHAR) LIKE {param}
                       OR LOWER(customer_name) LIKE {param}
                       OR LOWER(account_type) LIKE {param}
                    ORDER BY account_number ASC
                """
                like_term = f"%{q.lower()}%"
                cursor.execute(sql, (like_term, like_term, like_term))

            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r) if not db_manager.is_mysql else r
                results.append({
                    "account_number": item["account_number"],
                    "customer_name": item["customer_name"],
                    "balance": float(item["balance"]),
                    "account_type": item["account_type"]
                })
            return results
        finally:
            conn.close()

    # ==========================================
    # 7. CLOSE ACCOUNT
    # ==========================================
    @classmethod
    def close_account(cls, data: CloseAccountRequest) -> Dict[str, Any]:
        if not data.confirmation:
            raise ValueError("Account closure cancelled: user confirmation required.")

        conn = db_manager.get_connection()
        try:
            ok, account, msg = cls.authenticate(data.account_number, data.pin, conn)
            if not ok:
                raise ValueError(msg)

            balance = float(account["balance"])
            # Strict rule from original atm.py: balance must be exactly 0
            if balance != 0.0:
                raise ValueError(
                    f"Account closure rejected: Outstanding balance of ₹{balance:,.2f} detected. "
                    f"Please withdraw or transfer all funds to bring balance to exactly ₹0.00."
                )

            cursor = conn.cursor()
            param = "%s" if db_manager.is_mysql else "?"

            cls.record_transaction(
                conn,
                data.account_number,
                "ACCOUNT_CLOSURE",
                0.0,
                0.0,
                "SUCCESS",
                f"Account #{data.account_number} closed and purged by customer request"
            )

            delete_query = f"DELETE FROM Accounts WHERE account_number = {param}"
            cursor.execute(delete_query, (data.account_number,))

            conn.commit()
            return {
                "account_number": data.account_number,
                "message": f"Account #{data.account_number} closed successfully. All records cleared."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ==========================================
    # TRANSACTION HISTORY / AUDIT LOGS
    # ==========================================
    @classmethod
    def get_transactions(cls, account_number: int, limit: int = 15) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        cursor = cls._get_cursor(conn)
        try:
            param = "%s" if db_manager.is_mysql else "?"
            sql = f"""
                SELECT id, account_number, transaction_type, amount, balance_after, status, details, created_at 
                FROM Transactions 
                WHERE account_number = {param}
                ORDER BY id DESC LIMIT {limit}
            """
            cursor.execute(sql, (account_number,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r) if not db_manager.is_mysql else r
                results.append({
                    "id": item["id"],
                    "account_number": item["account_number"],
                    "transaction_type": item["transaction_type"],
                    "amount": float(item["amount"]),
                    "balance_after": float(item["balance_after"]),
                    "status": item["status"],
                    "details": item["details"],
                    "created_at": str(item["created_at"])
                })
            return results
        finally:
            conn.close()
