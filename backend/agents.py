import json
import os
import re
from typing import Any, Dict, List, Optional
import openai
from .config import settings
from .services import ATMService

# ==========================================
# OPENAI-COMPATIBLE CLIENT MANAGER
# ==========================================
class LLMClientManager:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL

    def update_config(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key.strip()
        if base_url is not None:
            self.base_url = base_url.strip()
        if model is not None:
            self.model = model.strip()

    def get_client(self) -> Optional[openai.OpenAI]:
        if not self.api_key:
            return None
        return openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url if self.base_url else "https://api.openai.com/v1"
        )

llm_manager = LLMClientManager()

# ==========================================
# TOOL DEFINITIONS FOR SINGLE AGENT
# ==========================================
SINGLE_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_account_directory",
            "description": "Searches for accounts by customer name, account number, or account type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g. 'Dhanu', '123456789', 'Savings')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "preview_withdrawal_capacity",
            "description": "Checks whether an account has sufficient balance to withdraw a requested amount and calculates ATM note breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "integer",
                        "description": "Account number"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Desired withdrawal amount"
                    }
                },
                "required": ["account_number", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_atm_policy",
            "description": "Explains ATM simulator rules such as zero-balance closure, PIN security, transaction limits, and account types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["closure_policy", "pin_security", "transaction_limits", "account_types"],
                        "description": "The specific policy topic to explain"
                    }
                },
                "required": ["topic"]
            }
        }
    }
]

def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes local tool logic for agent function calling."""
    if tool_name == "search_account_directory":
        query = arguments.get("query", "")
        results = ATMService.search_accounts(query)
        return json.dumps({"found_count": len(results), "accounts": results})

    elif tool_name == "preview_withdrawal_capacity":
        acc_num = arguments.get("account_number")
        amount = arguments.get("amount", 0.0)
        results = ATMService.search_accounts(str(acc_num))
        if not results:
            return json.dumps({"error": f"Account #{acc_num} not found."})
        acc = results[0]
        balance = acc["balance"]
        sufficient = balance >= amount
        denominations = ATMService.calculate_denominations(amount) if sufficient else {}
        return json.dumps({
            "account_number": acc_num,
            "current_balance": balance,
            "requested_amount": amount,
            "sufficient_funds": sufficient,
            "projected_remaining": max(0.0, balance - amount) if sufficient else balance,
            "denominations": denominations
        })

    elif tool_name == "explain_atm_policy":
        topic = arguments.get("topic")
        policies = {
            "closure_policy": "Zero-Balance Closure Policy: Under educational ATM banking regulations, an account can ONLY be closed when its balance is exactly ₹0.00. Customers must first withdraw or transfer all remaining funds.",
            "pin_security": "PIN Security Standard: PINs must be exactly 4 digits. They are never stored in plaintext and are hashed using PBKDF2-HMAC-SHA256 with 200,000 iterations and a 16-byte cryptographic salt.",
            "transaction_limits": f"ATM Simulator Limits: Maximum single deposit limit is ₹10,000,000. Transactions exceeding ₹{settings.HIGH_RISK_THRESHOLD:,.2f} are flagged by the Multi-Agent Fraud Auditor for security clearance.",
            "account_types": "Supported Account Types: 1) Savings (ideal for individuals, earns interest, requires minimum reserve), 2) Current / Checking (geared for commercial transactions with flexible daily operations)."
        }
        return json.dumps({"topic": topic, "policy_text": policies.get(topic, "General ATM Simulator Operating Rules apply.")})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})

# ==========================================
# SINGLE AGENT IMPLEMENTATION
# ==========================================
class SingleAgentCopilot:
    SYSTEM_PROMPT = """You are the 'ATM Smart Assistant' for an educational banking simulator.
Your role is to assist users with ATM account operations, balance verification inquiries, withdrawal planning, and banking rules.

CRITICAL EDUCATIONAL & SAFETY RULES:
1. This is strictly an EDUCATIONAL SIMULATOR. Never ask for or accept real personal passwords, credit card numbers, or real money.
2. NEVER ask for or output raw plaintext PINs in chat. Direct users to the interactive ATM keypad for PIN entry.
3. Use tool calls whenever the user asks to look up accounts, check withdrawal feasibility, or inquire about bank policies.
4. Keep answers concise, polite, professional, and formatted in clean Markdown.
"""

    @classmethod
    def run(cls, message: str, account_number: Optional[int] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        client = llm_manager.get_client()
        
        # If client is available, attempt real OpenAI/Gemini API call
        if client:
            try:
                messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]
                if history:
                    for h in history[-6:]:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                
                context_msg = message
                if account_number:
                    context_msg = f"[Context: Customer is currently viewing or using Account #{account_number}]\n{message}"
                messages.append({"role": "user", "content": context_msg})

                response = client.chat.completions.create(
                    model=llm_manager.model,
                    messages=messages,
                    tools=SINGLE_AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.3
                )
                choice = response.choices[0].message
                tool_calls_executed = []

                if choice.tool_calls:
                    # Execute tool call
                    for tc in choice.tool_calls:
                        func_name = tc.function.name
                        func_args = json.loads(tc.function.arguments)
                        tool_result = execute_tool_call(func_name, func_args)
                        tool_calls_executed.append({
                            "tool": func_name,
                            "arguments": func_args,
                            "result": json.loads(tool_result)
                        })

                        messages.append(choice)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": tool_result
                        })

                    second_resp = client.chat.completions.create(
                        model=llm_manager.model,
                        messages=messages,
                        temperature=0.3
                    )
                    final_text = second_resp.choices[0].message.content
                else:
                    final_text = choice.content

                return {
                    "mode": "live_llm",
                    "model": llm_manager.model,
                    "response": final_text,
                    "tool_calls": tool_calls_executed
                }
            except Exception as e:
                print(f"[SingleAgent] Live LLM call error: {e}. Falling back to simulation engine.")

        # Fallback Heuristic Simulator (Guaranteed Zero-Failure offline mode)
        return cls._simulate_single_agent(message, account_number)

    @classmethod
    def _simulate_single_agent(cls, message: str, account_number: Optional[int]) -> Dict[str, Any]:
        msg_lower = message.lower()
        tool_calls = []
        
        # Check if user asks about policy / closure
        if "close" in msg_lower or "closure" in msg_lower:
            tool_calls.append({
                "tool": "explain_atm_policy",
                "arguments": {"topic": "closure_policy"},
                "result": {"topic": "closure_policy", "policy_text": "Zero-Balance Closure Policy: Under educational ATM regulations, an account can ONLY be closed when its balance is exactly ₹0.00."}
            })
            response_text = (
                "**ATM Account Closure Policy Notice:**\n\n"
                "To close your account, your balance must be exactly **₹0.00**.\n"
                "- If you currently have remaining funds, please use the **Withdraw Money** tab first.\n"
                "- Once your balance is zero, navigate to the **Close Account** screen, verify your PIN, and submit closure."
            )

        # Check if user asks about PIN
        elif "pin" in msg_lower and ("change" in msg_lower or "security" in msg_lower or "forgot" in msg_lower):
            tool_calls.append({
                "tool": "explain_atm_policy",
                "arguments": {"topic": "pin_security"},
                "result": {"topic": "pin_security", "policy_text": "PIN Security Standard: PINs must be 4 digits and hashed with PBKDF2-HMAC-SHA256."}
            })
            response_text = (
                "**PIN Security Notice:**\n\n"
                "Your 4-digit PIN is strictly confidential. For security:\n"
                "- Use the **Change PIN** tab in the ATM menu to update your PIN securely.\n"
                "- Never share or type your PIN in chat windows.\n"
                "- All PINs are stored using salted cryptographic PBKDF2-HMAC-SHA256 hashing."
            )

        # Check if user asks about balance or withdrawal planning
        elif "withdraw" in msg_lower or "balance" in msg_lower:
            # Extract number if present
            numbers = re.findall(r"\b\d+\b", message)
            target_acc = account_number if account_number else (int(numbers[0]) if numbers else 123456789)
            target_amount = float(numbers[1]) if len(numbers) > 1 else 1000.0

            preview_res = execute_tool_call("preview_withdrawal_capacity", {"account_number": target_acc, "amount": target_amount})
            preview_data = json.loads(preview_res)
            tool_calls.append({
                "tool": "preview_withdrawal_capacity",
                "arguments": {"account_number": target_acc, "amount": target_amount},
                "result": preview_data
            })

            if "error" in preview_data:
                response_text = f"I could not locate Account #{target_acc}. Please verify your account number in the Account Directory."
            else:
                curr_bal = preview_data["current_balance"]
                if preview_data["sufficient_funds"]:
                    denom_str = ", ".join([f"{count}x {denom}" for denom, count in preview_data["denominations"].items()])
                    response_text = (
                        f"**Withdrawal Capacity Check for Account #{target_acc}:**\n\n"
                        f"- Current Available Balance: **₹{curr_bal:,.2f}**\n"
                        f"- Requested Amount: **₹{target_amount:,.2f}**\n"
                        f"- Status: **Sufficient funds available**\n"
                        f"- Projected Remaining Balance: **₹{preview_data['projected_remaining']:,.2f}**\n"
                        f"- Recommended Cash Breakdown: {denom_str}\n\n"
                        f"You may now proceed to the interactive ATM terminal to complete the withdrawal."
                    )
                else:
                    response_text = (
                        f"**Withdrawal Capacity Alert:**\n\n"
                        f"Account #{target_acc} has a balance of **₹{curr_bal:,.2f}**, which is insufficient for a withdrawal of **₹{target_amount:,.2f}**."
                    )

        # General search / accounts inquiry
        elif "search" in msg_lower or "account" in msg_lower or "find" in msg_lower:
            search_res = execute_tool_call("search_account_directory", {"query": ""})
            search_data = json.loads(search_res)
            tool_calls.append({
                "tool": "search_account_directory",
                "arguments": {"query": ""},
                "result": search_data
            })
            count = search_data["found_count"]
            response_text = (
                f"**ATM Accounts Directory:**\n\n"
                f"I located **{count} account(s)** in the database. "
                "You can inspect account numbers, holders, and account types in the Account Directory tab."
            )
        else:
            response_text = (
                "Hello! I am your **ATM Smart Copilot**. I can assist you with:\n"
                "- Checking withdrawal eligibility and note dispensing denominations\n"
                "- Inquiring about account rules (e.g. zero-balance closure policy)\n"
                "- Exploring account types (Savings vs Current)\n"
                "- Guiding you through deposits, PIN updates, and ATM operations.\n\n"
                "How can I help you with your ATM transactions today?"
            )

        return {
            "mode": "simulation_engine",
            "model": "ATM-RuleEngine-v2026",
            "response": response_text,
            "tool_calls": tool_calls
        }


# ==========================================
# MULTI-AGENT AGENTIC AI SYSTEM
# ==========================================
class MultiAgentCommittee:
    """
    Coordinates 3 collaborative agents to evaluate high-value or sensitive transactions:
    1. Concierge & Intent Orchestrator Agent
    2. Security & Fraud Risk Audit Agent
    3. Financial Advisory & Optimization Agent
    """

    @classmethod
    def run(cls, scenario: str, account_number: int, amount: Optional[float] = None, action_type: str = "WITHDRAWAL") -> Dict[str, Any]:
        # Fetch account details for contextual evaluation
        accounts = ATMService.search_accounts(str(account_number))
        account_info = accounts[0] if accounts else {
            "account_number": account_number,
            "customer_name": "Unknown Customer",
            "balance": 0.0,
            "account_type": "Savings"
        }

        recent_transactions = ATMService.get_transactions(account_number, limit=5)
        client = llm_manager.get_client()

        if client:
            try:
                return cls._run_live_multi_agent(client, scenario, account_info, recent_transactions, amount, action_type)
            except Exception as e:
                print(f"[MultiAgent] Live LLM multi-agent call failed: {e}. Falling back to committee simulation.")

        return cls._simulate_multi_agent(scenario, account_info, recent_transactions, amount, action_type)

    @classmethod
    def _run_live_multi_agent(
        cls,
        client: openai.OpenAI,
        scenario: str,
        account: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        amount: Optional[float],
        action_type: str
    ) -> Dict[str, Any]:
        prompt = f"""You are coordinating a 3-agent committee for an educational ATM banking simulator.
Evaluate this transaction scenario:
- Account Number: {account['account_number']}
- Customer Name: {account['customer_name']}
- Account Type: {account['account_type']}
- Current Balance: ₹{account['balance']:,.2f}
- Proposed Action: {action_type}
- Amount: ₹{amount if amount else 0:,.2f}
- Customer Scenario Statement: "{scenario}"
- Recent Transaction Count: {len(transactions)}

You must return a valid JSON object with the exact keys:
{{
  "concierge_agent": {{
    "role": "Customer Concierge & Intent Parser",
    "observation": "Summary of user intent and transaction decomposition",
    "action_requested": "{action_type}"
  }},
  "security_agent": {{
    "role": "Fraud & Security Risk Auditor",
    "risk_score": 25,
    "verdict": "APPROVED | STEP_UP_AUTH | BLOCKED",
    "reasons": ["Risk factor 1", "Risk factor 2"]
  }},
  "financial_agent": {{
    "role": "Financial Advisory Specialist",
    "impact_analysis": "How this affects customer liquidity and savings goals",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
  }},
  "synthesis": {{
    "final_verdict": "APPROVED | CONDITIONAL | REJECTED",
    "composite_risk_score": 25,
    "summary_rationale": "Unified explanation synthesized by orchestrator"
  }}
}}
Return ONLY the JSON object.
"""
        response = client.chat.completions.create(
            model=llm_manager.model,
            messages=[
                {"role": "system", "content": "You are a multi-agent banking committee orchestrator. Respond with pure JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        parsed = json.loads(response.choices[0].message.content)
        parsed["mode"] = "live_llm"
        parsed["model"] = llm_manager.model
        return parsed

    @classmethod
    def _simulate_multi_agent(
        cls,
        scenario: str,
        account: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        amount: Optional[float],
        action_type: str
    ) -> Dict[str, Any]:
        amount = amount or 0.0
        balance = account["balance"]
        ratio = (amount / balance) if balance > 0 else 1.0

        # Heuristic Security Audit logic
        reasons = []
        risk_score = 10

        if amount > settings.HIGH_RISK_THRESHOLD:
            risk_score += 45
            reasons.append(f"Transaction amount ₹{amount:,.2f} exceeds high-risk threshold (₹{settings.HIGH_RISK_THRESHOLD:,.2f}).")

        if ratio > 0.7:
            risk_score += 25
            reasons.append(f"Request represents {ratio*100:.1f}% of entire account liquid balance.")

        if balance < amount:
            risk_score = 95
            reasons.append(f"Requested amount exceeds total available balance (₹{balance:,.2f}).")
            sec_verdict = "BLOCKED"
        elif risk_score >= 60:
            sec_verdict = "STEP_UP_AUTH"
            reasons.append("Two-factor authentication and manager confirmation required.")
        else:
            sec_verdict = "APPROVED"
            reasons.append("Transaction metrics within standard nominal limits.")

        # Heuristic Financial Advisory logic
        rem_balance = max(0.0, balance - amount)
        if rem_balance < 5000 and account["account_type"].lower() == "savings":
            f_impact = f"Post-transaction balance of ₹{rem_balance:,.2f} will fall below recommended safety threshold of ₹5,000 for Savings."
            f_recs = [
                "Consider partial withdrawal to preserve emergency liquidity buffer.",
                "Review upcoming recurring obligations before finalizing."
            ]
        else:
            f_impact = f"Healthy post-transaction balance of ₹{rem_balance:,.2f} remains intact."
            f_recs = [
                "Surplus funds qualify for high-yield Fixed Deposit conversion.",
                "Opt into automated monthly sweep-in savings."
            ]

        # Committee Synthesis
        if sec_verdict == "BLOCKED":
            final_verdict = "REJECTED"
            summary = "Transaction blocked by Security Auditor due to insufficient funds or extreme anomaly."
        elif sec_verdict == "STEP_UP_AUTH":
            final_verdict = "CONDITIONAL"
            summary = "Transaction flagged for step-up verification due to high transaction value relative to normal velocity."
        else:
            final_verdict = "APPROVED"
            summary = "Consensus reached across all 3 agents: Intent verified, risk within tolerance, and financial health maintained."

        return {
            "mode": "simulation_engine",
            "model": "MultiAgent-Committee-v2026",
            "concierge_agent": {
                "role": "Customer Concierge & Intent Parser",
                "observation": f"Customer initiated a {action_type} of ₹{amount:,.2f} with note: '{scenario}'. Intent parsed and routed for safety checks.",
                "action_requested": action_type
            },
            "security_agent": {
                "role": "Fraud & Security Risk Auditor",
                "risk_score": min(100, risk_score),
                "verdict": sec_verdict,
                "reasons": reasons
            },
            "financial_agent": {
                "role": "Financial Advisory Specialist",
                "impact_analysis": f_impact,
                "recommendations": f_recs
            },
            "synthesis": {
                "final_verdict": final_verdict,
                "composite_risk_score": min(100, risk_score),
                "summary_rationale": summary
            }
        }
