"""Velie E2E Test — Intentional test file for QA review verification.

This file contains intentional code issues for Velie to detect:
- Security: hardcoded credentials
- Performance: N+1 pattern
- Bug: off-by-one error
- Quality: unused import, magic numbers
"""

import os
import json
import sys  # unused import

# 🔴 Security issue: hardcoded API key
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://admin:password123@prod-db:5432/main"


def get_users(db, user_ids: list[int]) -> list[dict]:
    """Fetch users one by one — N+1 query pattern."""
    users = []
    for uid in user_ids:
        # 🟡 Performance: N+1 query
        user = db.execute(f"SELECT * FROM users WHERE id = {uid}")  # Also SQL injection!
        users.append(user)
    return users


def process_items(items: list[str]) -> list[str]:
    """Process items with off-by-one error."""
    result = []
    # 🔴 Bug: off-by-one — should be range(len(items))
    for i in range(len(items) + 1):
        result.append(items[i].upper())
    return result


def calculate_discount(price: float) -> float:
    """Apply discount with magic numbers."""
    # 🟡 Quality: magic numbers
    if price > 100:
        return price * 0.85
    elif price > 50:
        return price * 0.9
    return price
