
import mysql.connector
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import secrets
import getpass


# CONNECT TO MYSQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="ATM_db"
)

cursor = conn.cursor()


# PIN SECURITY HELPERS
# Store a salted hash rather than the original PIN.
def hash_pin(pin):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", pin.encode(), bytes.fromhex(salt), 200000
    ).hex()
    return salt + "$" + hashed


def verify_pin(pin, stored):
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", pin.encode(), bytes.fromhex(salt), 200000
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def enter_pin():
    pin = getpass.getpass("Enter 4-digit PIN: ")
    if len(pin) != 4 or not pin.isdigit():
        print("PIN must contain exactly 4 digits.")
        return None
    return pin


def authenticate(account_number):
    cursor.execute(
        "SELECT pin FROM Accounts WHERE account_number = %s",
        (account_number,)
    )
    row = cursor.fetchone()

    if row is None:
        print("Account not found!")
        return False

    pin = enter_pin()
    if pin is None:
        return False

    if verify_pin(pin, row[0]):
        return True

    print("Incorrect PIN!")
    return False


def get_amount(prompt):
    try:
        amount = Decimal(input(prompt))
        if not amount.is_finite() or amount <= 0:
            print("Amount must be greater than zero.")
            return None
        if amount.as_tuple().exponent < -2:
            print("Enter an amount with no more than 2 decimal places.")
            return None
        if amount > Decimal("9999999999.99"):
            print("Amount is too large.")
            return None
        return amount
    except InvalidOperation:
        print("Enter a valid amount.")
        return None


# 1. CREATE ACCOUNT
def create_account():
    try:
        account_number = int(input("Enter new account number: "))
        if account_number <= 0:
            print("Account number must be positive.")
            return

        name = input("Enter customer name: ").strip()
        if not name:
            print("Customer name cannot be empty.")
            return

        account_type = input(
            "Enter account type (Savings/Current): "
        ).strip().capitalize()

        if account_type not in ("Savings", "Current"):
            print("Choose Savings or Current.")
            return

        pin = enter_pin()
        if pin is None:
            return

        balance = get_amount("Enter opening balance (0 allowed): ")
        # Allow a zero opening balance.
        if balance is None:
            raw = input("Enter 0 for zero opening balance, or a positive amount: ")
            try:
                balance = Decimal(raw)
                if not balance.is_finite() or balance != 0:
                    print("Invalid opening balance.")
                    return
            except InvalidOperation:
                print("Invalid opening balance.")
                return

        cursor.execute(
            """
            INSERT INTO Accounts
            (account_number, customer_name, balance, pin, account_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                account_number, name, balance,
                hash_pin(pin), account_type
            )
        )
        conn.commit()
        print("Account created successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 2. CHECK BALANCE
def check_balance():
    try:
        account_number = int(input("Enter account number: "))
        if not authenticate(account_number):
            return

        cursor.execute(
            "SELECT balance FROM Accounts WHERE account_number = %s",
            (account_number,)
        )
        row = cursor.fetchone()
        if row:
            print(f"Available balance: ₹{row[0]:,.2f}")

    except ValueError:
        print("Enter a valid account number.")


# 3. DEPOSIT MONEY
def deposit():
    try:
        account_number = int(input("Enter account number: "))
        if not authenticate(account_number):
            return

        amount = get_amount("Enter deposit amount: ")
        if amount is None:
            return

        cursor.execute(
            """
            UPDATE Accounts
            SET balance = balance + %s
            WHERE account_number = %s
            """,
            (amount, account_number)
        )
        conn.commit()
        print(f"₹{amount:,.2f} deposited successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 4. WITHDRAW MONEY
def withdraw():
    try:
        account_number = int(input("Enter account number: "))
        if not authenticate(account_number):
            return

        amount = get_amount("Enter withdrawal amount: ")
        if amount is None:
            return

        # Update only if sufficient funds exist.
        cursor.execute(
            """
            UPDATE Accounts
            SET balance = balance - %s
            WHERE account_number = %s AND balance >= %s
            """,
            (amount, account_number, amount)
        )

        if cursor.rowcount == 1:
            conn.commit()
            print(f"₹{amount:,.2f} withdrawn successfully!")
        else:
            conn.rollback()
            print("Insufficient balance or account not found.")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 5. CHANGE PIN
def change_pin():
    try:
        account_number = int(input("Enter account number: "))
        if not authenticate(account_number):
            return

        new_pin = enter_pin()
        if new_pin is None:
            return

        confirm_pin = getpass.getpass("Confirm new PIN: ")
        if new_pin != confirm_pin:
            print("PINs do not match!")
            return

        cursor.execute(
            "UPDATE Accounts SET pin = %s WHERE account_number = %s",
            (hash_pin(new_pin), account_number)
        )
        conn.commit()
        print("PIN changed successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 6. SEARCH ACCOUNT
def search_account():
    try:
        account_number = int(input("Enter account number to search: "))
        cursor.execute(
            """
            SELECT account_number, customer_name, balance, account_type
            FROM Accounts WHERE account_number = %s
            """,
            (account_number,)
        )
        row = cursor.fetchone()

        if row:
            print("\nAccount Details")
            print("Account Number:", row[0])
            print("Customer Name:", row[1])
            print(f"Balance: ₹{row[2]:,.2f}")
            print("Account Type:", row[3])
        else:
            print("Account not found!")

    except ValueError:
        print("Enter a valid account number.")


# 7. CLOSE ACCOUNT
def close_account():
    try:
        account_number = int(input("Enter account number to close: "))
        if not authenticate(account_number):
            return

        cursor.execute(
            "SELECT balance FROM Accounts WHERE account_number = %s",
            (account_number,)
        )
        row = cursor.fetchone()

        if row is None:
            print("Account not found!")
            return

        if row[0] != Decimal("0.00"):
            print("Please withdraw or transfer the remaining balance first.")
            return

        confirm = input(
            "Close this zero-balance account? (yes/no): "
        ).strip().lower()

        if confirm == "yes":
            cursor.execute(
                "DELETE FROM Accounts WHERE account_number = %s",
                (account_number,)
            )
            conn.commit()
            print("Account closed successfully!")
        else:
            print("Account closure cancelled.")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# MAIN MENU
try:
    print("Connected to ATM MySQL database successfully!")

    while True:
        print("""
========== ATM ACCOUNT MANAGEMENT ==========
1. Create Account
2. Check Balance
3. Deposit Money
4. Withdraw Money
5. Change PIN
6. Search Account
7. Close Account
8. Exit
============================================
""")

        choice = input("Enter your choice (1-8): ").strip()

        try:
            if choice == "1":
                create_account()
            elif choice == "2":
                check_balance()
            elif choice == "3":
                deposit()
            elif choice == "4":
                withdraw()
            elif choice == "5":
                change_pin()
            elif choice == "6":
                search_account()
            elif choice == "7":
                close_account()
            elif choice == "8":
                print("Thank you for using the ATM system!")
                break
            else:
                print("Invalid choice! Enter a number from 1 to 8.")

        except mysql.connector.Error as e:
            conn.rollback()
            print("Database error:", e)

finally:
    cursor.close()
    conn.close()
    print("MySQL connection closed.")
