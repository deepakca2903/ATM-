"""
Comprehensive Automated Test Suite for ATM Account Management Educational Simulator
Validates all 7 Core Scope operations + Single-Agent ReAct + Multi-Agent Committee
"""

import sys
import unittest
from fastapi.testclient import TestClient
from backend.server import app
from backend.database import db_manager

client = TestClient(app)

class TestATMAccountManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize DB tables
        db_manager.init_db()
        cls.test_acc_num = 998877665
        cls.test_name = "Test Student"
        cls.test_pin = "4321"
        cls.test_type = "Savings"
        cls.test_bal = 10000.0

        # Clean up any leftover test account from prior runs for idempotence
        conn = db_manager.get_connection()
        cur = conn.cursor()
        param = "%s" if db_manager.is_mysql else "?"
        cur.execute(f"DELETE FROM Accounts WHERE account_number = {param}", (cls.test_acc_num,))
        cur.execute(f"DELETE FROM Transactions WHERE account_number = {param}", (cls.test_acc_num,))
        conn.commit()
        conn.close()

    def test_01_health_check(self):
        """Verify API health and educational disclaimer."""
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("EDUCATIONAL SIMULATOR ONLY", data["disclaimer"])
        print("[PASS] Health Check Passed:", data["database"])

    def test_02_create_account(self):
        """Test Scope Item 1: Create Account."""
        payload = {
            "account_number": self.test_acc_num,
            "customer_name": self.test_name,
            "balance": self.test_bal,
            "pin": self.test_pin,
            "account_type": self.test_type
        }
        res = client.post("/api/accounts", json=payload)
        # If already exists from earlier test, 400 is expected, otherwise 201
        if res.status_code == 400 and "already exists" in res.json().get("detail", ""):
            print("[PASS] Account already present from prior run; continuing.")
        else:
            self.assertEqual(res.status_code, 201)
            data = res.json()
            self.assertEqual(data["account_number"], self.test_acc_num)
            self.assertEqual(data["balance"], self.test_bal)
            print("[PASS] Account Creation Passed.")

    def test_03_check_balance(self):
        """Test Scope Item 2: Check Balance."""
        # 1. Correct PIN
        res = client.post("/api/accounts/balance", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["account_number"], self.test_acc_num)
        self.assertGreaterEqual(data["balance"], 0.0)

        # 2. Incorrect PIN -> Should Fail
        res_fail = client.post("/api/accounts/balance", json={
            "account_number": self.test_acc_num,
            "pin": "0000"
        })
        self.assertEqual(res_fail.status_code, 401)
        print("[PASS] Check Balance Authentication Passed.")

    def test_04_deposit(self):
        """Test Scope Item 3: Deposit Money."""
        deposit_amount = 2500.0
        res = client.post("/api/accounts/deposit", json={
            "account_number": self.test_acc_num,
            "amount": deposit_amount
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["deposited_amount"], deposit_amount)
        print("[PASS] Deposit Operation Passed. New balance:", data["balance"])

    def test_05_withdraw(self):
        """Test Scope Item 4: Withdraw Money."""
        withdraw_amount = 1700.0
        res = client.post("/api/accounts/withdraw", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin,
            "amount": withdraw_amount
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["withdrawn_amount"], withdraw_amount)
        self.assertIn("denominations", data)
        print("[PASS] Withdrawal Passed. Dispensed Notes:", list(data["denominations"].values()))

        # Test Insufficient balance
        res_insufficient = client.post("/api/accounts/withdraw", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin,
            "amount": 999999999.0
        })
        self.assertEqual(res_insufficient.status_code, 400)
        self.assertIn("Insufficient", res_insufficient.json()["detail"])
        print("[PASS] Insufficient Funds Guardrail Passed.")

    def test_06_change_pin(self):
        """Test Scope Item 5: Change PIN."""
        new_pin = "8899"
        res = client.post("/api/accounts/change-pin", json={
            "account_number": self.test_acc_num,
            "old_pin": self.test_pin,
            "new_pin": new_pin,
            "confirm_pin": new_pin
        })
        self.assertEqual(res.status_code, 200)

        # Verify old PIN no longer works
        old_check = client.post("/api/accounts/balance", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin
        })
        self.assertEqual(old_check.status_code, 401)

        # Verify new PIN works
        new_check = client.post("/api/accounts/balance", json={
            "account_number": self.test_acc_num,
            "pin": new_pin
        })
        self.assertEqual(new_check.status_code, 200)

        # Update test pin for subsequent tests
        self.__class__.test_pin = new_pin
        print("[PASS] Change PIN Cryptographic Update Passed.")

    def test_07_search_account(self):
        """Test Scope Item 6: Search Account."""
        res = client.get(f"/api/accounts/search?query={self.test_acc_num}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["count"], 1)
        found = any(a["account_number"] == self.test_acc_num for a in data["accounts"])
        self.assertTrue(found)
        print("[PASS] Search Account Passed.")

    def test_08_single_agent_copilot(self):
        """Test Generative AI / Single-Agent Copilot ReAct tool loop."""
        res = client.post("/api/ai/single-agent", json={
            "message": f"Can I withdraw ₹500 from account {self.test_acc_num}?",
            "account_number": self.test_acc_num
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("response", data)
        self.assertIn("tool_calls", data)
        print("[PASS] Single-Agent ReAct Tool Execution Passed. Mode:", data.get("mode"))

    def test_09_multi_agent_committee(self):
        """Test Multi-Agent Committee Orchestration (Concierge, Security, Financial)."""
        res = client.post("/api/ai/multi-agent", json={
            "scenario": "Customer emergency medical cash withdrawal",
            "account_number": self.test_acc_num,
            "amount": 25000.0,
            "action_type": "WITHDRAWAL"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("concierge_agent", data)
        self.assertIn("security_agent", data)
        self.assertIn("financial_agent", data)
        self.assertIn("synthesis", data)
        self.assertIn(data["synthesis"]["final_verdict"], ["APPROVED", "CONDITIONAL", "REJECTED"])
        print("[PASS] Multi-Agent Committee Consensus Passed. Verdict:", data["synthesis"]["final_verdict"])

    def test_10_close_account_guardrail_and_closure(self):
        """Test Scope Item 7: Close Account with Zero-Balance Rule."""
        # 1. Attempt closure while balance > 0 -> Must Fail
        res_fail = client.post("/api/accounts/close", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin,
            "confirmation": True
        })
        self.assertEqual(res_fail.status_code, 400)
        self.assertIn("balance", res_fail.json()["detail"].lower())
        print("[PASS] Non-zero Balance Closure Blocked as required by policy.")

        # 2. Withdraw remaining balance to exactly 0
        bal_res = client.post("/api/accounts/balance", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin
        })
        rem_bal = bal_res.json()["balance"]
        if rem_bal > 0:
            client.post("/api/accounts/withdraw", json={
                "account_number": self.test_acc_num,
                "pin": self.test_pin,
                "amount": rem_bal
            })

        # 3. Now close zero-balance account -> Must Succeed
        res_success = client.post("/api/accounts/close", json={
            "account_number": self.test_acc_num,
            "pin": self.test_pin,
            "confirmation": True
        })
        self.assertEqual(res_success.status_code, 200)
        print("[PASS] Zero-Balance Account Closure Passed Successfully.")

if __name__ == "__main__":
    unittest.main()
