import mysql.connector
import sqlite3
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from .config import settings

class DatabaseManager:
    def __init__(self):
        self.is_mysql = False
        self.active_db_name = ""

    def test_mysql_connection(self) -> bool:
        """Attempts to connect to MySQL server."""
        try:
            # First connect to server without database to ensure DB exists
            conn = mysql.connector.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                connect_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}`")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[DatabaseManager] MySQL connection failed: {e}. Falling back to SQLite.")
            return False

    def get_connection(self):
        """Returns a connection to either MySQL or SQLite depending on availability."""
        if settings.DB_TYPE.lower() == "mysql" and self.is_mysql:
            return mysql.connector.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE
            )
        else:
            conn = sqlite3.connect(settings.SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            return conn

    def init_db(self):
        """Initializes tables in either MySQL or SQLite."""
        if settings.DB_TYPE.lower() == "mysql" and self.test_mysql_connection():
            self.is_mysql = True
            self.active_db_name = f"MySQL ({settings.MYSQL_DATABASE})"
            self._init_mysql_schema()
        else:
            self.is_mysql = False
            self.active_db_name = f"SQLite ({settings.SQLITE_PATH})"
            self._init_sqlite_schema()
        print(f"[DatabaseManager] Active database engine: {self.active_db_name}")

    def _init_mysql_schema(self):
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        # 1. Accounts Table (matches original atm.py schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Accounts (
                account_number BIGINT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                pin VARCHAR(255) NOT NULL,
                account_type VARCHAR(20) NOT NULL
            ) ENGINE=InnoDB;
        """)

        # 2. Transactions Table (for audit trail, history, and agent inspection)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account_number BIGINT NOT NULL,
                transaction_type VARCHAR(30) NOT NULL,
                amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                balance_after DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
                details VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_acc (account_number)
            ) ENGINE=InnoDB;
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def _init_sqlite_schema(self):
        conn = sqlite3.connect(settings.SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Accounts (
                account_number INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                balance NUMERIC NOT NULL DEFAULT 0.00,
                pin TEXT NOT NULL,
                account_type TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount NUMERIC NOT NULL DEFAULT 0.00,
                balance_after NUMERIC NOT NULL DEFAULT 0.00,
                status TEXT NOT NULL DEFAULT 'SUCCESS',
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()

db_manager = DatabaseManager()
