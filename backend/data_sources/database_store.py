"""
Persistent Local Intelligence Database Store.
Maintains relational case metadata, wallet cluster identities, and cross-case shared infrastructure memory.
"""
import sqlite3
import os
from typing import Dict, Any, List, Optional


class DatabaseStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "vasptrace.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. Cases Metadata Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    fir_number TEXT,
                    title TEXT,
                    suspect_wallet TEXT,
                    chain TEXT,
                    amount_inr REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 2. Shared Infrastructure Registry Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS syndicate_registry (
                    wallet_address TEXT,
                    case_id TEXT,
                    role TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (wallet_address, case_id)
                )
            """)
            conn.commit()
