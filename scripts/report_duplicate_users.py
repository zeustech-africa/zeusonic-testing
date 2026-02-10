#!/usr/bin/env python3
"""Read-only report of duplicate user emails (case-insensitive)."""
from sqlalchemy import func
from backend.db.database import SessionLocal
from backend.db import models


def main() -> None:
    with SessionLocal() as db:
        rows = (
            db.query(func.lower(models.User.email).label("email"), func.count(models.User.id).label("count"))
            .group_by(func.lower(models.User.email))
            .having(func.count(models.User.id) > 1)
            .order_by(func.count(models.User.id).desc())
            .all()
        )

    if not rows:
        print("No duplicate emails found.")
        return

    print("Duplicate emails detected:")
    for row in rows:
        print(f"- {row.email}: {row.count} records")


if __name__ == "__main__":
    main()
