import os
import re
import shutil
import hashlib
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

from .config import (
    DEVICE,
    DB_PATH,
    EMBEDDING_MODEL_NAME,
    RERANKER_MODEL_NAME,
)

print("🧠 Embedding (BGE-M3) yükleniyor...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": DEVICE},
    encode_kwargs={"normalize_embeddings": True},
)

print("⚖️ Reranker model yükleniyor...", RERANKER_MODEL_NAME)
reranker_model = CrossEncoder(
    RERANKER_MODEL_NAME,
    device=DEVICE
)

UPLOAD_DIR = Path("uploaded_documents")
UPLOAD_DIR.mkdir(exist_ok=True)

def build_document_id(file_path: Path) -> str:
    raw = f"{file_path.name}-{file_path.stat().st_size}-{file_path.stat().st_mtime}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def build_splitter():
    separators = [
        r"\n(?=\d+\.\d+\.\d+\.?)",
        r"\n(?=\d+\.\d+\.?)",
        r"\n(?=\d+\.\s+[A-ZÇĞİÖŞÜ])",
        r"\n(?=[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]{3,}$)",
        "\n\n",
        "\n",
        " ",
        ""
    ]

    return RecursiveCharacterTextSplitter(
        separators=separators,
        is_separator_regex=True,
        chunk_size=1000,
        chunk_overlap=200
    )


def build_header_pattern():
    return re.compile(r"^(\d+(\.\d+)*\.?)\s+([A-ZÇĞİÖŞÜa-zçğıöşü].+)")

def extract_document_segments(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return [{
            "text": text,
            "page": None
        }]

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        segments = []

        for page_idx, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                segments.append({
                    "text": page_text,
                    "page": page_idx
                })

        return segments

    if suffix == ".docx":
        doc = Document(str(file_path))
        full_text = "\n".join(
            [p.text for p in doc.paragraphs if p.text is not None and p.text.strip()]
        )
        return [{
            "text": full_text,
            "page": None
        }]

    raise ValueError("Desteklenmeyen dosya türü. Sadece .pdf, .docx, .txt destekleniyor.")


def chunk_document_segments(file_path: Path, segments, splitter, header_pattern, start_chunk_id: int):
    texts = []
    metadatas = []

    document_id = build_document_id(file_path)
    current_section_title = "Giriş / Genel Bilgi"
    chunk_id_counter = start_chunk_id
    chunk_index_in_document = 0

    for segment in segments:
        segment_text = segment.get("text", "")
        page_number = segment.get("page")

        if not segment_text or not segment_text.strip():
            continue

        raw_chunks = splitter.split_text(segment_text)

        for chunk_text in raw_chunks:
            clean_chunk = chunk_text.strip()
            if not clean_chunk:
                continue

            first_line = clean_chunk.split("\n")[0].strip() if clean_chunk else ""
            match = header_pattern.match(first_line)

            if match:
                current_section_title = match.group(0).strip()

            texts.append(clean_chunk)
            metadatas.append({
                "chunk_id": chunk_id_counter,
                "document_id": document_id,
                "chunk_index_in_document": chunk_index_in_document,
                "page": page_number,
                "source": file_path.name,
                "file_type": file_path.suffix.lower().replace(".", ""),
                "section_title": current_section_title,
                "is_active": True
            })

            chunk_id_counter += 1
            chunk_index_in_document += 1

    return texts, metadatas, chunk_id_counter


def collect_uploaded_documents():
    splitter = build_splitter()
    header_pattern = build_header_pattern()

    all_texts = []
    all_metadatas = []
    chunk_id_counter = 0

    allowed_extensions = {".pdf", ".docx", ".txt"}

    for file_path in sorted(UPLOAD_DIR.iterdir()):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in allowed_extensions:
            continue

        try:
            segments = extract_document_segments(file_path)
        except Exception as e:
            print(f"⚠️ Dosya okunamadı: {file_path.name} | hata={e}")
            continue

        if not segments:
            continue

        texts, metadatas, chunk_id_counter = chunk_document_segments(
            file_path=file_path,
            segments=segments,
            splitter=splitter,
            header_pattern=header_pattern,
            start_chunk_id=chunk_id_counter
        )

        all_texts.extend(texts)
        all_metadatas.extend(metadatas)

    return all_texts, all_metadatas


def clear_saved_vectorstore():
    if os.path.exists(DB_PATH):
        if os.path.isdir(DB_PATH):
            shutil.rmtree(DB_PATH)
        else:
            os.remove(DB_PATH)


def rebuild_vectorstore_from_uploaded_documents():
    global vectorstore

    texts, metadatas = collect_uploaded_documents()

    if len(texts) == 0:
        vectorstore = None
        clear_saved_vectorstore()
        print("⚠️ uploaded_documents klasöründe indexlenecek dosya yok. Vectorstore boş.")
        return None

    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )

    vectorstore.save_local(DB_PATH)
    print(f"✅ Vectorstore yeniden oluşturuldu. Toplam chunk sayısı: {len(texts)}")
    if metadatas:
        print("🔎 Örnek metadata:", metadatas[0])
    return vectorstore


def load_or_build_vectorstore():
    if os.path.exists(DB_PATH):
        try:
            print(f"💾 Kayıtlı veritabanı yükleniyor: {DB_PATH}")
            return FAISS.load_local(
                DB_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception:
            print("⚠️ Kayıtlı veritabanı yüklenemedi. uploaded_documents klasöründen yeniden oluşturulacak.")

    return rebuild_vectorstore_from_uploaded_documents()


vectorstore = load_or_build_vectorstore()