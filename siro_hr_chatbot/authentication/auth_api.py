# authentication/auth_api.py

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import secrets
import os
import httpx
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from db import get_connection

from authentication.auth import (create_access_token, get_employee_from_sap, find_or_create_user_from_sap, check_for_admin_account, create_admin_access_token, register_new_admin_account, verify_admin_token_simple)

router = APIRouter(tags=["SF Authentication"])


class SFLoginRequest(BaseModel):
    pernr: str
    api_key: str

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class RegisterAdminRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


temporary_login_tokens = {}


@router.post("/api/sf-login")
def sf_login(data: SFLoginRequest):
    expected_api_key = os.getenv("SF_LOGIN_API_KEY")
    backend_api = os.getenv("CHATBOT_BACKEND_API")

    if not expected_api_key:
        raise HTTPException(
            status_code=500,
            detail="SF_LOGIN_API_KEY .env içinde tanımlı değil."
        )

    if data.api_key != expected_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz API key."
        )

    pernr = data.pernr

    if not pernr:
        raise HTTPException(
            status_code=400,
            detail="pernr alanı zorunludur."
        )

    temporary_token = secrets.token_urlsafe(32)

    temporary_login_tokens[temporary_token] = {
        "pernr": pernr,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=180),
        "used": False
    }

    redirect_url = f"{backend_api}/auth/callback?token={temporary_token}"

    return {
        "redirect_url": redirect_url,
        "expires_in_seconds": 90,
        "message": "Geçici giriş bağlantısı oluşturuldu."
    }


@router.get("/auth/callback")
async def auth_callback(token: str):
    """
    Kullanıcının tarayıcısı bu endpoint'e gelir.
    Geçici token doğrulanır.
    SAP'ten kullanıcı bilgisi alınır.
    Chatbot için gerçek JWT oluşturulur.
    Frontend'e yönlendirilir.
    """

    token_record = temporary_login_tokens.get(token)

    if not token_record:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz giriş bağlantısı."
        )

    if token_record["used"]:
        raise HTTPException(
            status_code=401,
            detail="Bu giriş bağlantısı daha önce kullanılmış."
        )

    if datetime.now(timezone.utc) > token_record["expires_at"]:
        raise HTTPException(
            status_code=401,
            detail="Giriş bağlantısının süresi dolmuş."
        )

    pernr = token_record["pernr"]

    sap_user = await get_employee_from_sap(pernr)

    if not sap_user.get("status"):
        raise HTTPException(
            status_code=403,
            detail="SAP üzerinde aktif çalışan bulunamadı."
        )

    conn = get_connection()

    try:
        user = find_or_create_user_from_sap(conn, sap_user)

        access_token = create_access_token(
            acc_id=user["acc_id"],
            pernr=user["pernr"],
            email=user["email"]
        )

    finally:
        conn.close()

    frontend_callback_url = os.getenv("FRONTEND_CALLBACK_URL")

    token_record["used"] = True

    redirect_url = f"{frontend_callback_url}?{urlencode({'access_token': access_token})}"

    return RedirectResponse(url=redirect_url)


# ADMIN LOGIN
@router.post("/admin/login")
def admin_login(payload: AdminLoginRequest):
    conn = get_connection()

    try:
        admin = check_for_admin_account(
            conn=conn,
            entered_mail=payload.email,
            entered_password=payload.password
        )

        if not admin:
            raise HTTPException(
                status_code=401,
                detail="Admin e-posta veya şifre hatalı."
            )

        access_token = create_admin_access_token(
            admin_acc_id=admin["admin_acc_id"],
            email=admin["email"]
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "admin": {
                "admin_acc_id": admin["admin_acc_id"],
                "email": admin["email"],
                "name": admin["name"]
            }
        }

    finally:
        conn.close()


@router.post("/admin/register")
def register_admin(
    payload: RegisterAdminRequest,
    authorization: str = Header(None)
):
    """
    Sadece giriş yapmış admin yeni admin hesabı oluşturabilir.
    """

    # 1. Mevcut admin token doğrulaması
    current_admin = verify_admin_token_simple(authorization)

    conn = get_connection()

    try:
        # 2. Yeni admin hesabı oluştur
        new_admin = register_new_admin_account(
            conn=conn,
            name=payload.name,
            email=payload.email,
            password=payload.password
        )

        return {
            "message": "Yeni admin hesabı başarıyla oluşturuldu.",
            "created_admin": {
                "admin_acc_id": new_admin["admin_acc_id"],
                "name": new_admin["name"],
                "email": new_admin["email"],
                "user_type": new_admin["user_type"]
            },
            "created_by": {
                "admin_acc_id": current_admin["admin_acc_id"],
                "email": current_admin["email"]
            }
        }

    finally:
        conn.close()