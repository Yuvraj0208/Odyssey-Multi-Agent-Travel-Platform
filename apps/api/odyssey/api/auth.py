"""Auth endpoints: register, login, me. JWT sessions, bcrypt-hashed passwords."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from odyssey.api.deps import CurrentUser, current_user
from odyssey.core.security import create_access_token, hash_password, verify_password
from odyssey.graph.runtime import get_runtime
from odyssey.memory.user_repo import create_user, get_user_by_email, public_user
from odyssey.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn) -> TokenOut:
    runtime = await get_runtime()
    if await get_user_by_email(runtime.store, body.email):
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = await create_user(runtime.store, body.email, hash_password(body.password), body.name)
    token = create_access_token(user["id"], user["email"])
    return TokenOut(access_token=token, user=UserOut(**public_user(user)))


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn) -> TokenOut:
    runtime = await get_runtime()
    user = await get_user_by_email(runtime.store, body.email)
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = create_access_token(user["id"], user["email"])
    return TokenOut(access_token=token, user=UserOut(**public_user(user)))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser = Depends(current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email or "", name=user.name)
