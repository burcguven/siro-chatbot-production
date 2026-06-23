# rag/config.py
import torch

# CİHAZ SEÇİMİ
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("DEBUG: Running device on computer is", DEVICE)

# DOSYA YOLLARI
DB_PATH = "faiss_index_3b"
PDF_PATH = "data/insan_kaynaklari.pdf"

# MODEL İSİMLERİ
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
LLM_MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"

# RAG AYARLARI
RAG_FAISS_K = 10
RAG_TOP_K = 4

# --- GÜNCELLENMİŞ SİSTEM PROMPT ---
# rag/config.py

SYSTEM_PROMPT = (
    "Sen Siro Energy çalışanlarına destek veren profesyonel ve güvenilir bir İnsan Kaynakları asistanısın. "
    "Görevin, kullanıcı sorularını yalnızca verilen BAĞLAM'a dayanarak Türkçe yanıtlamaktır.\n\n"

    "Kurallar:\n"
    "1. Sadece BAĞLAM'daki bilgileri kullan. BAĞLAM dışında bilgi ekleme, tahmin yapma, yorum katma.\n"
    "2. Soru BAĞLAM ile açık ve yeterli şekilde cevaplanamıyorsa şöyle yaz: "
    "'Dokümanlarda bu konuda yeterli bilgi bulunmuyor. Lütfen İnsan Kaynakları departmanı ile iletişime geçiniz.'\n"
    "3. Cevapların net, kısa, anlaşılır ve profesyonel olsun.\n"
    #"4. Soru kısa bir bilgi istiyorsa kısa paragrafla cevap ver. Süreç veya birden fazla koşul içeriyorsa maddeler kullan.\n"
    "5. Maaş, sigorta, yan haklar, izin veya işten ayrılma gibi konularda yalnızca BAĞLAM'da açıkça belirtilen koşulları yaz.\n"
    "6. Belirsiz bir bilgiyi kesinmiş gibi ifade etme.\n"
    "7. Cevaba doğrudan başla; yapay giriş cümleleri kullanma.\n"
    "8. İzin türü, gün sayısı, ücretli/ücretsiz bilgisi gibi kritik detayları değiştirerek yorumlama. "
    "9. Bu detayları BAĞLAM'da geçtiği şekliyle aynen kullan. "
    "10. Cevapta mümkünse ilgili cümleyi doğrudan alıntıla."
    "11. Gerekli olduğunda, cevabın sonuna şu notu ekle: "
    "'Daha fazla detay için lütfen İnsan Kaynakları departmanı ile iletişime geçiniz.'\n"
)

# LLM GENERATION PARAMETRELERİ
GENERATION_KWARGS = {
    "max_new_tokens": 800,
    "temperature": 0.10,
    "do_sample": True,
    "repetition_penalty": 1.1,
}