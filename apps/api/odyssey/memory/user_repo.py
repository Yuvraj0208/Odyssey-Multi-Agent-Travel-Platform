"""User accounts stored in the LangGraph store (namespace ("users",)).

Keyed by lowercased email. Consistent with the store-backed session index and
long-term memory, so it works in both local (in-process) and stack (Postgres) modes
without a separate schema. Passwords are stored only as bcrypt hashes.
"""

from __future__ import annotations

import time
import uuid


def _ns() -> tuple[str, ...]:
    return ("users",)


async def get_user_by_email(store, email: str) -> dict | None:
    item = await store.aget(_ns(), email.lower())
    return item.value if item else None


async def create_user(store, email: str, password_hash: str, name: str | None = None) -> dict:
    user = {
        "id": "u_" + uuid.uuid4().hex[:12],
        "email": email.lower(),
        "name": name or email.split("@")[0],
        "password_hash": password_hash,
        "created_at": time.time(),
    }
    await store.aput(_ns(), email.lower(), user)
    return user


def public_user(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user.get("name")}
