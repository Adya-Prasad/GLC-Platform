"""Database migration helpers for local SQLite DB used during development.

This script is idempotent and safe to run multiple times. It will check for
missing columns and add them with sensible defaults. Run via:

    python glc_db_operations.py

"""

import sqlite3
import sys
import argparse
from typing import List

DB_PATH = "glc_data.db"

