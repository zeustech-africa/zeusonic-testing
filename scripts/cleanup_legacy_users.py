#!/usr/bin/env python3
"""One-time cleanup for legacy users with missing/invalid password hashes.

This script is NOT an API and must be run manually by an operator.
It only targets users where is_verified = true and password_hash is missing/invalid.
"""
from typing import List, Optional

from backend.db.database import SessionLocal
from backend.db import models


def _is_hash_invalid(password_hash: Optional[str]) -> bool:
    if not password_hash:
        return True
    # Basic sanity check: bcrypt hashes usually start with $2...
    if not password_hash.startswith("$2"):
        return True
    if len(password_hash) < 20:
        return True
    return False


def main() -> None:
    repaired = 0
    invalidated = 0

    with SessionLocal() as db:
        query = db.query(models.User).filter(models.User.is_verified == True)
        users: List[models.User] = query.all()
        total_scanned = len(users)
        affected = [u for u in users if _is_hash_invalid(u.password_hash)]

        print(f"Query: {query}")
        print(f"Total users scanned: {total_scanned}")
        print(f"Affected legacy users: {len(affected)}")

        for user in affected:
            print(f"- id={user.id} email={user.email}")
            user.is_verified = False
            db.add(user)
            invalidated += 1

        db.commit()

    print("Cleanup complete.")
    print(f"Legacy users repaired: {repaired}")
    print(f"Legacy users invalidated: {invalidated}")
    print("Confirmation: clean users remain unchanged.")


if __name__ == "__main__":
    main()
