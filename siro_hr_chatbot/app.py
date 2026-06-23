#app.py
import numpy as np
import asyncio
from starlette.concurrency import run_in_threadpool
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path
import shutil
from datetime import datetime
import os

from db import (
    get_name_from_email,
    delete_chat,
    get_connection,
    authenticate_user,
    get_or_create_chat,
    save_message,
    load_chat_history,
    create_new_chat,
    update_chat_title_from_first_message,
    get_user_chats_for_sidebar,
    get_chat_messages,
    rename_chat_title,
    chat_belongs_to_user,
    get_all_chatbot_categories,
    is_category_enabled,
    update_chatbot_category_status
)

# --- Mevcut Importlar ---
from rag.pipeline import run_rag, run_rag_stream, run_context_stream, run_hybrid_stream
from rag.category_classifier import classify_question_category
from rag.question_scope_classifier import classify_question_scope
# --- Yeni Eklenen Auth Importları ---
from authentication.auth import create_access_token, verify_token
from rag.docstore import rebuild_vectorstore_from_uploaded_documents, UPLOAD_DIR
from fastapi.responses import StreamingResponse
import json

from authentication.auth_api import router as auth_router
from authentication.auth import verify_admin_token_simple, get_employee_from_sap


app = FastAPI(
    title="SIRO HR Chatbot API",
    description="Qwen 2.5 + BGE-M3 + Reranker RAG Backend + JWT Auth",
    version="1.1.0"
)

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")


llm_semaphore = asyncio.Semaphore(1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


class AdminLoginRequest(BaseModel):
    email: str
    password: str

# --- İSTEK MODELLERİ (YENİ) ---
# JSON verisini doğrulamak için Pydantic kullanıyoruz
class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    question: str
    history: List[dict] = Field(default_factory=list)
    chat_id: int

class ChatRenameRequest(BaseModel):
    new_title: str

class CategoryUpdateRequest(BaseModel):
    category_key: str
    is_enabled: bool

# --- NumPy Temizleyici (AYNEN KORUNDU) ---
def convert_numpy_to_python(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(v) for v in obj]
    return obj


async def resolve_question_route(conn, question: str):
    # Önce soru tipi belirlenir.
    scope_result = await run_in_threadpool(
        classify_question_scope,
        question
    )

    scope = scope_result.get("scope", "general")

    print("\n[SCOPE CLASSIFICATION]")
    print("Question:", question)
    print("Scope:", scope)
    print("Score:", scope_result.get("score"))
    print("Method:", scope_result.get("method"))

    # General sorular önce RAG'e gider.
    if scope == "general":
        return {
            "route": "rag",
            "blocked": False,
            "category": None,
            "scope": scope_result,
            "answer": None
        }

    # Sadece personal ve hybrid sorular hemen kategorize edilir.
    category_result = await run_in_threadpool(
        classify_question_category,
        question
    )

    category_key = category_result["category_key"]
    category_name = category_result["category_name"]

    print("\n[CATEGORY CLASSIFICATION]")
    print("Category key:", category_key)
    print("Category name:", category_name)
    print("Score:", category_result.get("score"))
    print("Method:", category_result.get("method"))

    # Kişisel veriye erişim kapalıysa engelle.
    if not is_category_enabled(conn, category_key):
        return {
            "route": "blocked",
            "blocked": True,
            "category": category_result,
            "scope": scope_result,
            "answer": (
                f"Bu soru '{category_name}' kategorisinde kişisel bilgi "
                "gerektiriyor. Bu kategori şu anda admin tarafından kapalı "
                "olduğu için kişisel bilgilerinize erişemiyorum."
            )
        }

    route = "personal_api" if scope == "personal" else "hybrid"

    return {
        "route": route,
        "blocked": False,
        "category": category_result,
        "scope": scope_result,
        "answer": None
    }




@app.get("/")
async def root():
    return {"message": "SIRO HR Chatbot API is running. 🚀"}

# --- 1. YENİ LOGIN ENDPOINT ---
@app.post("/login")
def login(data: LoginRequest):
    """
    Kullanıcı girişi yapar ve JWT Token döner.
    """
    user = authenticate_user(data.email, data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Hatalı e-posta veya şifre!")

    access_token = create_access_token(
    acc_id=user["acc_id"],
    pernr=user["pernr"],
    email=user["email"]
)
        
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "message": "Giriş başarılı"
    }
    
@app.get("/get_username")
async def get_username_and_email_for_FE(current_user: dict = Depends(verify_token)):
    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    user_email = current_user["email"]
    try:
        user_info = get_name_from_email(conn, user_email)
        name = user_info["name"]
        email = user_info["mail"]
        user_type = user_info["user_type"]
        return {
            "name": name,
            "email": email,
            "user_type": user_type
        }
    except:
        raise HTTPException(status_code=401, detail="Bir hata oluştu!")  
    finally:
        conn.close()


@app.post("/chat/create")
async def create_chat(current_user: dict = Depends(verify_token)):

    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    try:

        chat_id = create_new_chat(conn, acc_id)

        return {
            "chat_id": chat_id,
            "title": "Yeni Sohbet"
        }

    finally:
        conn.close()


@app.get("/all_chats")
async def get_chats(current_user: dict = Depends(verify_token)):

    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    try:

        chats = get_user_chats_for_sidebar(conn, acc_id)

        return {
            "chats": chats
        }

    finally:
        conn.close()


@app.get("/chat/get_all_messages/{chat_id}")
async def get_chat_detail(chat_id: int, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    try:
        messages = get_chat_messages(conn, chat_id, acc_id)

        return {
            "chat_id": chat_id,
            "messages": messages
        }
    finally:
        conn.close()

@app.put("/chat/{chat_id}/rename_chat")
async def rename_title(chat_id: int, title_request: ChatRenameRequest, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    user_email = current_user["email"]
    try:
        new_title = title_request.new_title.strip()
        if not new_title:
            raise HTTPException(status_code=400, detail="Sohbet başlığı boş olamaz.")
        affected_rows = rename_chat_title(conn, chat_id, acc_id, new_title)
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Sohbet bulunamadı.")
        return {
            "chat_id": chat_id,
            "new_title": new_title
        }
    finally:
        conn.close()


@app.delete("/chat/{chat_id}")
async def delete_chat_endpoint(chat_id: int, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    user_email = current_user["email"]
    try:

        if not chat_belongs_to_user(conn, chat_id, acc_id):
            raise HTTPException(status_code=403, detail="Bu sohbet için yetkiniz yok.")

        affected_rows = delete_chat(conn, chat_id, acc_id)

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Sohbet bulunamadı.")

        return {
            "message": "Sohbet silindi.",
            "chat_id": chat_id
        }

    finally:
        conn.close()

# COMMENTED OUT BECAUSE NEW VERSIONS ARE WRITTEN IN authentication/auth_api.py

# @app.post("/admin/login")
# def admin_login(payload: AdminLoginRequest):
#     ADMIN_EMAIL = "tarik@admin.com"
#     ADMIN_PASSWORD = "123456"

#     if payload.email != ADMIN_EMAIL or payload.password != ADMIN_PASSWORD:
#         raise HTTPException(status_code=401, detail="Admin bilgileri hatalı.")

#     return {
#         "access_token": "fake-admin-token",
#         "token_type": "bearer"
#     }

# def verify_admin_token_simple(authorization: str):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header eksik.")

#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Bearer token formatı geçersiz.")

#     parts = authorization.split(" ")
#     if len(parts) != 2:
#         raise HTTPException(status_code=401, detail="Authorization formatı geçersiz.")

#     token = parts[1].strip()

#     if token != "fake-admin-token":
#         raise HTTPException(status_code=401, detail="Geçersiz admin token.")

@app.get("/admin/files")
async def list_uploaded_files(authorization: str = Header(None)):
    verify_admin_token_simple(authorization)

    files = []

    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()

            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "file_type": file_path.suffix.lower(),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    files.sort(key=lambda x: x["last_modified"], reverse=True)

    return {"files": files, "count": len(files)}


@app.post("/admin/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    verify_admin_token_simple(authorization)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı bulunamadı.")

    allowed_extensions = {".pdf", ".docx", ".txt"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Desteklenmeyen dosya türü. Sadece .pdf, .docx, .txt destekleniyor."
        )

    save_path = UPLOAD_DIR / file.filename
    backup_path = UPLOAD_DIR / f"{file.filename}.bak"
    replacing_existing = save_path.exists()

    try:
        if replacing_existing:
            save_path.replace(backup_path)

        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        rebuild_vectorstore_from_uploaded_documents()

        if backup_path.exists():
            backup_path.unlink()

    except Exception as e:
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception:
                pass

        if backup_path.exists() and not save_path.exists():
            try:
                backup_path.replace(save_path)
            except Exception:
                pass

        raise HTTPException(status_code=500, detail=f"Dosya yüklenip indexlenemedi: {str(e)}")

    return {
        "message": "Dosya başarıyla yüklendi ve bilgi havuzu güncellendi.",
        "filename": file.filename,
        "replaced_existing": replacing_existing
    }

@app.delete("/admin/files/{filename}")
async def delete_file(filename: str, authorization: str = Header(None)):
    verify_admin_token_simple(authorization)

    file_path = UPLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")

    backup_path = UPLOAD_DIR / f"{filename}.bak"

    try:
        file_path.replace(backup_path)
        rebuild_vectorstore_from_uploaded_documents()

        if backup_path.exists():
            backup_path.unlink()

    except Exception as e:
        # rollback
        if backup_path.exists() and not file_path.exists():
            backup_path.replace(file_path)

        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")

    return {
        "message": "Dosya silindi ve bilgi havuzu güncellendi.",
        "filename": filename
    }

#category classifier endpoints

@app.get("/admin/categories")
async def list_chatbot_categories(authorization: str = Header(None)):
    verify_admin_token_simple(authorization)

    conn = get_connection()
    try:
        categories = get_all_chatbot_categories(conn)
        return {
            "categories": categories
        }
    finally:
        conn.close()


@app.put("/admin/categories")
async def update_chatbot_category(
    request: CategoryUpdateRequest,
    authorization: str = Header(None)
):
    verify_admin_token_simple(authorization)

    conn = get_connection()
    try:
        affected_rows = update_chatbot_category_status(
            conn,
            request.category_key,
            request.is_enabled
        )

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı.")

        return {
            "message": "Kategori durumu güncellendi.",
            "category_key": request.category_key,
            "is_enabled": request.is_enabled
        }
    finally:
        conn.close()


def format_sap_employee_context(sap_user: dict) -> str:
    """
    SAP employee response'u LLM'e verilecek güvenli metin bağlamına çevirir.
    """

    allowed_fields = {
        "pernr": "Personel numarası",
        "name": "Ad",
        "surname": "Soyad",
        "department": "Departman",
        "position": "Pozisyon",
        "gender": "Cinsiyet",
        "birthDate": "Doğum tarihi",
        "maritalStatus": "Medeni durum",
        "workProgramRule": "Çalışma düzeni",
    }

    lines = []

    for key, label in allowed_fields.items():
        value = sap_user.get(key)

        if value is not None and str(value).strip():
            lines.append(f"{label}: {value}")

    if not lines:
        return "Kullanıcıya ait kişisel bilgi bulunamadı."

    return "\n".join(lines)





@app.post("/ask-stream")
async def ask_question_stream(request: ChatRequest, current_user: dict = Depends(verify_token)
):
    acc_id = current_user["acc_id"]
    pernr = current_user["pernr"]
    user_email = current_user.get("email")

    question = (request.question or "").strip()
    chat_id = request.chat_id

    print(f"\n🔐 GİRİŞ YAPAN KULLANICI (STREAM): {user_email}")
    print(f"🆔 ACC_ID: {acc_id}")
    print(f"🆔 PERNR: {pernr}")

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Soru boş olamaz."
        )

    # Streaming başlamadan önce kullanıcı, sohbet ve route kontrol edilir.
    conn = get_connection()

    try:
        if not chat_belongs_to_user(conn, chat_id, acc_id):
            raise HTTPException(
                status_code=403,
                detail="Bu sohbet için yetkiniz yok."
            )

        history = load_chat_history(
            conn,
            chat_id,
            limit=10
        )

        save_message(
            conn,
            chat_id,
            "user",
            question
        )

        update_chat_title_from_first_message(
            conn,
            chat_id
        )

        routing = await resolve_question_route(
            conn,
            question
        )

    finally:
        conn.close()

    route = routing["route"]
    category_result = routing["category"]
    scope_result = routing["scope"]

    # -------------------------------------------------
    # KAPALI KATEGORİ STREAM
    # -------------------------------------------------

    if route == "blocked":
        blocked_answer = routing["answer"]

        def blocked_event_stream():
            stream_conn = None

            try:
                stream_conn = get_connection()

                save_message(
                    stream_conn,
                    chat_id,
                    "assistant",
                    blocked_answer
                )

                yield json.dumps(
                    {
                        "type": "token",
                        "content": blocked_answer
                    },
                    ensure_ascii=False
                ) + "\n"

                yield json.dumps(
                    {
                        "type": "done",
                        "chat_id": chat_id,
                        "user": user_email,
                        "timestamp": datetime.utcnow().isoformat(),
                        "route": "blocked",
                        "blocked": True,
                        "category": category_result,
                        "scope": None
                    },
                    ensure_ascii=False
                ) + "\n"

            except Exception as error:
                print(f"❌ BLOCKED STREAM HATASI: {str(error)}")

                yield json.dumps(
                    {
                        "type": "error",
                        "message": "Cevap oluşturulurken hata oluştu."
                    },
                    ensure_ascii=False
                ) + "\n"

            finally:
                if stream_conn:
                    stream_conn.close()

        return StreamingResponse(
            blocked_event_stream(),
            media_type="application/x-ndjson"
        )

    # -------------------------------------------------
    # PERSONAL ROUTE
    # -------------------------------------------------

    if route == "personal_api":
        sap_user = await get_employee_from_sap(pernr)

        if not sap_user.get("status"):
            raise HTTPException(
                status_code=403,
                detail="SAP üzerinde aktif çalışan bilgisi bulunamadı."
            )

        personal_context = format_sap_employee_context(sap_user)

        def personal_event_stream():
            stream_conn = None

            try:
                stream_conn = get_connection()

                full_answer_parts = []

                token_gen, payload = run_context_stream(
                    user_input=question,
                    context=personal_context,
                    chat_history=history,
                    context_title="KİŞİSEL ÇALIŞAN BİLGİSİ"
                )

                for chunk in token_gen:
                    full_answer_parts.append(chunk)

                    yield json.dumps(
                        {
                            "type": "token",
                            "content": chunk
                        },
                        ensure_ascii=False
                    ) + "\n"

                personal_answer = "".join(full_answer_parts).strip()

                save_message(
                    stream_conn,
                    chat_id,
                    "assistant",
                    personal_answer
                )

                yield json.dumps(
                    {
                        "type": "done",
                        "chat_id": chat_id,
                        "user": user_email,
                        "pernr": pernr,
                        "timestamp": datetime.utcnow().isoformat(),
                        "route": "personal_api",
                        "blocked": False,
                        "category": category_result,
                        "scope": scope_result
                    },
                    ensure_ascii=False
                ) + "\n"

            except Exception as error:
                print(f"❌ PERSONAL STREAM HATASI: {str(error)}")

                yield json.dumps(
                    {
                        "type": "error",
                        "message": "Kişisel bilgiye dayalı cevap oluşturulurken hata oluştu."
                    },
                    ensure_ascii=False
                ) + "\n"

            finally:
                if stream_conn:
                    stream_conn.close()

        return StreamingResponse(
            personal_event_stream(),
            media_type="application/x-ndjson"
        )

    # -------------------------------------------------
    # HYBRID ROUTE
    # -------------------------------------------------

    if route == "hybrid":
        sap_user = await get_employee_from_sap(pernr)

        if not sap_user.get("status"):
            raise HTTPException(
                status_code=403,
                detail="SAP üzerinde aktif çalışan bilgisi bulunamadı."
            )

        personal_context = format_sap_employee_context(sap_user)

        def hybrid_event_stream():
            stream_conn = None

            try:
                stream_conn = get_connection()

                full_answer_parts = []

                token_gen, payload = run_hybrid_stream(
                    user_input=question,
                    personal_context=personal_context,
                    chat_history=history
                )

                for chunk in token_gen:
                    if not chunk:
                        continue

                    full_answer_parts.append(chunk)

                    yield json.dumps(
                        {
                            "type": "token",
                            "content": chunk
                        },
                        ensure_ascii=False
                    ) + "\n"

                hybrid_answer = "".join(full_answer_parts).strip()

                if not hybrid_answer:
                    hybrid_answer = (
                        "Kişisel bilgi ve doküman bağlamına göre şu anda "
                        "bu soruya yanıt oluşturamadım."
                    )

                save_message(
                    stream_conn,
                    chat_id,
                    "assistant",
                    hybrid_answer
                )

                print("\n" + "=" * 50)
                print(f"📥 SORU (HYBRID STREAM): {question}")
                print(f"📂 ROUTE: hybrid")
                print(f"📂 KATEGORİ: {category_result}")
                print(f"📂 SCOPE: {scope_result}")
                print(f"📂 RAG FALLBACK: {payload.get('rag_fallback_answer') is not None}")
                print(f"📂 RAG FALLBACK REASON: {payload.get('rag_fallback_reason')}")
                print("-" * 30)
                print(f"🤖 CEVAP (HYBRID STREAM): {hybrid_answer}")
                print("=" * 50 + "\n")

                yield json.dumps(
                    {
                        "type": "done",
                        "chat_id": chat_id,
                        "user": user_email,
                        "pernr": pernr,
                        "timestamp": datetime.utcnow().isoformat(),
                        "route": "hybrid",
                        "blocked": False,
                        "category": category_result,
                        "scope": scope_result,
                        "rag_fallback_reason": payload.get("rag_fallback_reason")
                    },
                    ensure_ascii=False
                ) + "\n"

            except Exception as error:
                print(f"❌ HYBRID STREAM HATASI: {str(error)}")

                yield json.dumps(
                    {
                        "type": "error",
                        "message": "Kişisel bilgi ve doküman bağlamına dayalı cevap oluşturulurken hata oluştu."
                    },
                    ensure_ascii=False
                ) + "\n"

            finally:
                if stream_conn:
                    stream_conn.close()

        return StreamingResponse(
            hybrid_event_stream(),
            media_type="application/x-ndjson"
        )


    # -------------------------------------------------
    # GENERAL / RAG ROUTE
    # -------------------------------------------------
    # If route is not blocked, personal_api, or hybrid,
    # it falls through to normal document RAG answering.

    def rag_event_stream():
        stream_conn = None

        try:
            stream_conn = get_connection()

            full_answer_parts = []

            final_route = route
            final_blocked = False
            final_category = category_result

            token_gen, payload = run_rag_stream(
                question,
                history
            )

            # -------------------------------------------------
            # RAG CEVAP BULAMADIYSA KATEGORİ KONTROLÜ
            # -------------------------------------------------

            if payload.get("fallback_answer") is not None:
                fallback_category = classify_question_category(question)

                category_key = fallback_category["category_key"]
                category_name = fallback_category["category_name"]

                final_category = fallback_category

                print("\n[RAG FALLBACK CATEGORY CHECK]")
                print("Question:", question)
                print("Category key:", category_key)
                print("Category name:", category_name)
                print("Fallback reason:", payload.get("fallback_reason"))

                # Kategori kapalıysa RAG fallback mesajını kullanma
                if not is_category_enabled(stream_conn, category_key):
                    final_answer = (
                        f"Bu soru '{category_name}' kategorisine ait görünüyor. "
                        "Bu kategori şu anda admin tarafından kapalı olduğu için "
                        "cevap veremiyorum."
                    )

                    final_route = "blocked_after_rag"
                    final_blocked = True

                    save_message(
                        stream_conn,
                        chat_id,
                        "assistant",
                        final_answer
                    )

                    yield json.dumps(
                        {
                            "type": "token",
                            "content": final_answer
                        },
                        ensure_ascii=False
                    ) + "\n"

                    yield json.dumps(
                        {
                            "type": "done",
                            "chat_id": chat_id,
                            "user": user_email,
                            "timestamp": datetime.utcnow().isoformat(),
                            "route": final_route,
                            "blocked": final_blocked,
                            "category": final_category,
                            "scope": scope_result,
                            "fallback_reason": payload.get("fallback_reason")
                        },
                        ensure_ascii=False
                    ) + "\n"

                    print("\n" + "=" * 50)
                    print(f"📥 SORU (STREAM): {question}")
                    print(f"📂 ROUTE: {final_route}")
                    print(f"📂 KATEGORİ: {final_category}")
                    print(f"📂 SCOPE: {scope_result}")
                    print("-" * 30)
                    print(f"🤖 CEVAP (STREAM): {final_answer}")
                    print("=" * 50 + "\n")

                    # RAG fallback generator'ına geçilmesini engeller
                    return

                # Kategori açıksa normal RAG fallback mesajı gösterilir
                final_route = "rag_fallback"

            # -------------------------------------------------
            # NORMAL RAG VEYA AÇIK KATEGORİ FALLBACK STREAM
            # -------------------------------------------------

            for chunk in token_gen:
                if not chunk:
                    continue

                full_answer_parts.append(chunk)

                yield json.dumps(
                    {
                        "type": "token",
                        "content": chunk
                    },
                    ensure_ascii=False
                ) + "\n"

            final_answer = "".join(full_answer_parts).strip()

            # Boş cevap kaydedilmesini önler
            if not final_answer:
                final_answer = (
                    payload.get("fallback_answer")
                    or "Bu soruya şu anda yanıt oluşturamadım."
                )

            save_message(
                stream_conn,
                chat_id,
                "assistant",
                final_answer
            )

            print("\n" + "=" * 50)
            print(f"📥 SORU (STREAM): {question}")
            print(f"📂 ROUTE: {final_route}")
            print(f"📂 KATEGORİ: {final_category}")
            print(f"📂 SCOPE: {scope_result}")
            print(f"📂 FALLBACK: {payload.get('fallback_answer') is not None}")
            print(f"📂 FALLBACK REASON: {payload.get('fallback_reason')}")
            print("-" * 30)
            print(f"🤖 CEVAP (STREAM): {final_answer}")
            print("=" * 50 + "\n")

            yield json.dumps(
                {
                    "type": "done",
                    "chat_id": chat_id,
                    "user": user_email,
                    "timestamp": datetime.utcnow().isoformat(),
                    "route": final_route,
                    "blocked": final_blocked,
                    "category": final_category,
                    "scope": scope_result,
                    "fallback_reason": payload.get("fallback_reason")
                },
                ensure_ascii=False
            ) + "\n"

        except Exception as error:
            print(f"❌ STREAM HATASI: {str(error)}")

            yield json.dumps(
                {
                    "type": "error",
                    "message": "Cevap oluşturulurken hata oluştu."
                },
                ensure_ascii=False
            ) + "\n"

        finally:
            if stream_conn:
                stream_conn.close()




    return StreamingResponse(
        rag_event_stream(),
        media_type="application/x-ndjson"
    )