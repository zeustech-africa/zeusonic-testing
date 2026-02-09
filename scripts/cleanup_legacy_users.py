#!/usr/bin/env python3
"""One-time cleanup for legacy users with missing/invalid password hashes.

This script is NOT an API and must be run manually by an operator.
It only targets users where is_verified = true and password_hash is missing/invalid.
"""
import argparse
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
    parser = argparse.ArgumentParser(description="Cleanup legacy verified users with missing/invalid password hashes.")
    parser.add_argument(
        "--action",
        choices=["invalidate", "delete"],
        default="invalidate",
        help="Action to take on invalid users (default: invalidate).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report affected users without making changes.",
    )

    args = parser.parse_args()

    repaired = 0
    invalidated = 0
    deleted = 0

    with SessionLocal() as db:
        users: List[models.User] = db.query(models.User).filter(models.User.is_verified == True).all()
        affected = [u for u in users if _is_hash_invalid(u.password_hash)]

        print(f"Affected legacy users: {len(affected)}")
        for user in affected:
            print(f"- {user.email}")

        if args.dry_run:
            print("Dry run complete. No changes applied.")
            print("Legacy users repaired: 0")
            print("Legacy users invalidated: 0")
            return

        if args.action == "invalidate":
            for user in affected:
                user.is_verified = False
                db.add(user)
                invalidated += 1
        else:
            for user in affected:
                db.delete(user)
                deleted += 1

        db.commit()

    print("Cleanup complete.")
    print(f"Legacy users repaired: {repaired}")
    print(f"Legacy users invalidated: {invalidated}")
    print(f"Legacy users deleted: {deleted}")


if __name__ == "__main__":
    main()
