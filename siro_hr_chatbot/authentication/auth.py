# auth.py
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os
import httpx
from passlib.context import CryptContext

# GÜVENLİK AYARLARI
SECRET_KEY = os.getenv("SECRET_KEY_TOKEN", "siro-secret-token-key") # Prodüksiyonda .env'den alınmalı
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # Token 2 saat geçerli olsun
ADMIN_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()


def create_access_token(acc_id: int, pernr: str, email: str | None = None):
    """
    Kullanıcıya özel JWT oluşturur.
    Token içinde chatbot acc_id ve SAP pernr bilgisi tutulur.
    """

    payload = {
        "sub": str(acc_id),  # Subject artık email değil, acc_id
        "acc_id": acc_id,
        "pernr": pernr,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Gelen isteğin token'ını doğrular.
    Geçerliyse kullanıcı kimlik bilgilerini döner.
    """

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        acc_id = payload.get("acc_id")
        pernr = payload.get("pernr")
        email = payload.get("email")

        if not acc_id or not pernr:
            raise HTTPException(status_code=401, detail="Geçersiz token")

        return {
            "acc_id": acc_id,
            "pernr": pernr,
            "email": email
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Oturum süreniz doldu. Lütfen tekrar giriş yapın."
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token doğrulanamadı"
        )


import os
import httpx
from fastapi import HTTPException


async def get_employee_from_sap(pernr: str):
    sap_base_url = os.getenv(
        "SAP_EMPLOYEE_API_URL",
        "https://siroqhanaapp.siro.energy/zhr_chatbot_srv/employee"
    )

    sap_username = os.getenv("SAP_API_USERNAME")
    sap_password = os.getenv("SAP_API_PASSWORD")

    if not sap_username or not sap_password:
        raise HTTPException(
            status_code=500,
            detail="SAP_API_USERNAME veya SAP_API_PASSWORD .env içinde tanımlı değil."
        )

    async with httpx.AsyncClient(verify=True, timeout=10) as client:
        response = await client.get(
            sap_base_url,
            params={"PERNR": pernr},
            auth=(sap_username, sap_password)
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"SAP employee API çağrısı başarısız. Status: {response.status_code}, Body: {response.text}"
        )

    return response.json()


def find_or_create_user_from_sap(conn, sap_user: dict):
    """
    Şimdilik basit versiyon.
    Bunun düzgün çalışması için employees tablosuna pernr kolonu eklenmeli.
    """

    pernr = sap_user["pernr"]
    name = sap_user.get("name", "")
    surname = sap_user.get("surname", "")
    department = sap_user.get("department", "")
    gender = sap_user.get("gender", "")

    # SAP response içinde email yoksa geçici email üretilebilir.
    # Daha iyisi: SAP endpointinden mail alanını da istemek.
    email = sap_user.get("email") or f"{pernr}@siro.local"

    full_name = f"{name} {surname}".strip()

    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT 
            u.user_id,
            u.mail,
            ea.acc_id,
            e.emp_id,
            e.pernr
        FROM employees e
        JOIN users u ON e.user_id = u.user_id
        JOIN employee_accounts ea ON ea.emp_id = e.emp_id
        WHERE e.pernr = %s
        """

        cursor.execute(query, (pernr,))
        existing_user = cursor.fetchone()

        if existing_user: # if there exists a user like this on our Chatbot Database --> return his info

            conn.commit()

            return {
                "user_id": existing_user["user_id"],
                "emp_id": existing_user["emp_id"],
                "acc_id": existing_user["acc_id"],
                "email": email,
                "pernr": pernr
            }
        # If no such user exists in our Chatbot Database --> add the user to Database
        print("There is no user named "+name+" in the current Chatbot Database")
        print("Adding the person with the following info to Chatbot Database")
        print(f"Name: {name}\t Surname: {surname}\t mail: {email} \t PERNR: {pernr}")
        insert_user_query = """
        INSERT INTO users (name, mail, user_type)
        VALUES (%s, %s, 'employee')
        """
        cursor.execute(insert_user_query, (full_name, email))
        user_id = cursor.lastrowid

        insert_employee_query = """
        INSERT INTO employees (
            user_id,
            pernr
        )
        VALUES (%s, %s)
        """
        cursor.execute(
            insert_employee_query,
            (user_id, pernr)
        )
        emp_id = cursor.lastrowid

        insert_account_query = """
        INSERT INTO employee_accounts (emp_id, password_hash)
        VALUES (%s, %s)
        """
        cursor.execute(
            insert_account_query,
            (emp_id, "SF_SSO_USER_NO_PASSWORD")
        )
        acc_id = cursor.lastrowid

        conn.commit()

        return {
            "user_id": user_id,
            "emp_id": emp_id,
            "acc_id": acc_id,
            "email": email,
            "pernr": pernr
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Kullanıcı oluşturulurken hata oluştu: {str(e)}"
        )

    finally:
        cursor.close()




def check_for_admin_account(conn, entered_mail: str, entered_password: str):
    """
    Girilen admin email ve password bilgisini veritabanındaki admin hesabı ile karşılaştırır.
    Doğruysa admin bilgilerini döner.
    Yanlışsa None döner.
    """

    query = """
    SELECT
        u.user_id,
        u.name,
        u.mail,
        u.user_type,
        a.admin_id,
        aa.admin_acc_id,
        aa.password_hash
    FROM users u
    JOIN admins a ON a.user_id = u.user_id
    JOIN admin_accounts aa ON aa.admin_id = a.admin_id
    WHERE u.mail = %s
      AND u.user_type = 'admin'
    LIMIT 1
    """

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, (entered_mail,))
        admin = cursor.fetchone()

        if not admin:
            print("No such admin with email address:", entered_mail)
            return None

        stored_hash = admin["password_hash"]

        password_is_correct = pwd_context.verify(
            entered_password,
            stored_hash
        )

        if not password_is_correct:
            print("Wrong password for", entered_mail)
            return None

        return {
            "user_id": admin["user_id"],
            "admin_id": admin["admin_id"],
            "admin_acc_id": admin["admin_acc_id"],
            "name": admin["name"],
            "email": admin["mail"],
            "user_type": admin["user_type"]
        }

    finally:
        cursor.close()


def create_admin_access_token(admin_acc_id: int, email: str):
    """
    Admin kullanıcı için JWT oluşturur.
    """

    payload = {
        "sub": str(admin_acc_id),
        "admin_acc_id": admin_acc_id,
        "email": email,
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def verify_admin_token_simple(authorization: str):
    """
    Admin endpointlerinde kullanılan Bearer admin token doğrulaması.
    Token geçerliyse admin bilgilerini döner.
    """

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header eksik.")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token formatı geçersiz.")

    parts = authorization.split(" ")

    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Authorization formatı geçersiz.")

    token = parts[1].strip()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("role") != "admin":
            raise HTTPException(status_code=401, detail="Admin yetkisi yok.")

        admin_acc_id = payload.get("admin_acc_id")
        email = payload.get("email")

        if not admin_acc_id or not email:
            raise HTTPException(status_code=401, detail="Geçersiz admin token.")

        return {
            "admin_acc_id": admin_acc_id,
            "email": email,
            "role": "admin"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Admin oturum süresi doldu.")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz admin token.")
    


def register_new_admin_account(conn, name: str, email: str, password: str):
    """
    Yeni admin hesabı oluşturur.
    users, admins ve admin_accounts tablolarına kayıt ekler.
    """

    if not name or not email or not password:
        raise HTTPException(
            status_code=400,
            detail="İsim, e-posta ve şifre zorunludur."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Admin şifresi en az 6 karakter olmalıdır."
        )

    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Bu email zaten var mı?
        check_query = """
        SELECT user_id, user_type
        FROM users
        WHERE mail = %s
        LIMIT 1
        """
        cursor.execute(check_query, (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Bu e-posta adresiyle kayıtlı bir kullanıcı zaten var."
            )

        # 2. Şifreyi hashle
        password_hash = pwd_context.hash(password)

        # 3. users tablosuna ekle
        insert_user_query = """
        INSERT INTO users (name, mail, user_type)
        VALUES (%s, %s, 'admin')
        """
        cursor.execute(insert_user_query, (name, email))
        user_id = cursor.lastrowid

        # 4. admins tablosuna ekle
        insert_admin_query = """
        INSERT INTO admins (user_id)
        VALUES (%s)
        """
        cursor.execute(insert_admin_query, (user_id,))
        admin_id = cursor.lastrowid

        # 5. admin_accounts tablosuna ekle
        insert_admin_account_query = """
        INSERT INTO admin_accounts (admin_id, password_hash)
        VALUES (%s, %s)
        """
        cursor.execute(insert_admin_account_query, (admin_id, password_hash))
        admin_acc_id = cursor.lastrowid

        conn.commit()

        return {
            "user_id": user_id,
            "admin_id": admin_id,
            "admin_acc_id": admin_acc_id,
            "name": name,
            "email": email,
            "user_type": "admin"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Admin hesabı oluşturulurken hata oluştu: {str(e)}"
        )

    finally:
        cursor.close()