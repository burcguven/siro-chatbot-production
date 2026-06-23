# rag/pipeline.py

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
)
from threading import Thread

from .config import (
    DEVICE,
    SYSTEM_PROMPT,
    RAG_FAISS_K,
    RAG_TOP_K,
    LLM_MODEL_ID,
    GENERATION_KWARGS
)

from . import docstore
from .docstore import reranker_model

print(f"Model loading ({LLM_MODEL_ID})...")

tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL_ID,
    torch_dtype=torch.float16,
    device_map=DEVICE
)

# -------------------------------------------------
# 1️⃣ LLM BASED QUERY EXPANSION
# -------------------------------------------------

def llm_expand_query(user_input: str) -> str:
    expansion_prompt = f"""
Kullanıcı şu ifadeyi yazdı:

"{user_input}"

Bu ifadeyi HR politikası bağlamında daha açıklayıcı bir soru cümlesine dönüştür.
Sadece yeniden yazılmış soruyu ver.
"""

    inputs = tokenizer(expansion_prompt, return_tensors="pt").to(DEVICE)

    outputs = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=60,
        temperature=0.2,
        eos_token_id=tokenizer.eos_token_id
    )

    expanded = tokenizer.decode(
        outputs[0][len(inputs.input_ids[0]):],
        skip_special_tokens=True
    ).strip()

    return expanded


# -------------------------------------------------
# 2️⃣ SHORT QUERY DETECTION
# -------------------------------------------------

def is_short_query(text: str) -> bool:
    return len(text.strip().split()) <= 3


def build_query_variants(user_input: str) -> list[str]:
    queries = [user_input.strip()]

    if is_short_query(user_input):
        try:
            expanded_query = llm_expand_query(user_input)
            if expanded_query and expanded_query not in queries:
                queries.append(expanded_query)
        except Exception as e:
            print(f"[QUERY EXPANSION ERROR] input='{user_input}' error={e}")

    return queries


def deduplicate_results(results):
    seen = set()
    unique_results = []

    for doc, score, used_query in results:
        chunk_id = doc.metadata.get("chunk_id")
        page_content = doc.page_content.strip()

        unique_key = chunk_id if chunk_id is not None else page_content

        if unique_key in seen:
            continue

        seen.add(unique_key)
        unique_results.append((doc, score, used_query))

    return unique_results

def diversify_top_results(score_dict, top_k: int, max_per_source: int = 3):
    diversified = []
    source_counts = {}

    for item in score_dict:
        source = item["doc"].metadata.get("source", "unknown")
        current_count = source_counts.get(source, 0)

        if current_count >= max_per_source:
            continue

        diversified.append(item)
        source_counts[source] = current_count + 1

        if len(diversified) >= top_k:
            break

    if len(diversified) < top_k:
        used_ids = {id(item["doc"]) for item in diversified}
        for item in score_dict:
            if id(item["doc"]) in used_ids:
                continue
            diversified.append(item)
            if len(diversified) >= top_k:
                break

    return diversified


# -------------------------------------------------
# 3️⃣ ADAPTIVE RETRIEVAL
# -------------------------------------------------

def adaptive_retrieval(query: str):
    if docstore.vectorstore is None:
        return [], query, []

    dynamic_k = RAG_FAISS_K + 3 if is_short_query(query) else RAG_FAISS_K

    query_variants = build_query_variants(query)
    all_results = []

    for q in query_variants:
        try:
            results = docstore.vectorstore.similarity_search_with_score(
                q,
                k=dynamic_k
            )

            for doc, score in results:
                all_results.append((doc, score, q))

        except Exception as e:
            print(f"[RETRIEVAL ERROR] query='{q}' error={e}")

    if len(all_results) == 0:
        return [], query, query_variants

    unique_results = deduplicate_results(all_results)

    best_query = query
    best_avg_score = float("inf")

    for q in query_variants:
        q_scores = [score for _, score, used_query in unique_results if used_query == q]
        if q_scores:
            avg_score = sum(q_scores) / len(q_scores)
            if avg_score < best_avg_score:
                best_avg_score = avg_score
                best_query = q

    unique_results = sorted(unique_results, key=lambda x: x[1])

    return unique_results, best_query, query_variants


# -------------------------------------------------
# 4️⃣ ORTAK YARDIMCI FONKSİYONLAR
# -------------------------------------------------

def remove_near_duplicate_chunks(items, max_items: int):
    selected = []
    seen_prefixes = set()

    for item in items:
        text = item["doc"].page_content.strip()
        prefix = text[:200]

        if prefix in seen_prefixes:
            continue

        seen_prefixes.add(prefix)
        selected.append(item)

        if len(selected) >= max_items:
            break

    return selected


def build_rag_payload(user_input: str, chat_history=None):
    if chat_history is None:
        chat_history = []

    faiss_results, final_query, query_variants = adaptive_retrieval(user_input)

    if len(faiss_results) == 0:
        return {
            "fallback_answer": "Şu anda sistemde yüklenmiş bir doküman bulunamadı ya da soruyla ilgili uygun bağlam bulunamadı.",
            "fallback_reason": "no_retrieval_results",
            "context": "",
            "chunks": [],
            "messages": None,
        }

    # Reranker için pairing
    pairs = [(used_query, doc.page_content) for doc, score, used_query in faiss_results]

    rerank_scores = reranker_model.predict(pairs)

    score_dict = []
    for i in range(len(faiss_results)):
        doc, faiss_score, used_query = faiss_results[i]
        rerank_score = float(rerank_scores[i])

        score_dict.append({
            "doc": doc,
            "faiss_score": faiss_score,
            "rerank_score": rerank_score,
            "used_query": used_query
        })

    score_dict = sorted(score_dict, key=lambda x: x["rerank_score"], reverse=True)

    top_results = diversify_top_results(score_dict, top_k=RAG_TOP_K, max_per_source=3)
    top_results = remove_near_duplicate_chunks(top_results, max_items=RAG_TOP_K)

    if len(top_results) == 0:
        return {
            "fallback_answer": "Soruyla ilgili uygun bir bağlam bulunamadı.",
            "fallback_reason": "no_top_results",
            "context": "",
            "chunks": [],
            "messages": None,
        }

    best_rerank_score = top_results[0]["rerank_score"]
    best_faiss_score = top_results[0]["faiss_score"]
    avg_top_rerank = sum(item["rerank_score"] for item in top_results) / len(top_results)
    unique_sources = len({item["doc"].metadata.get("source", "unknown") for item in top_results})

    print("\n[PIPELINE DEBUG]")
    print("User query:", user_input)
    print("Query variants:", query_variants)
    print("Final query for rerank:", final_query)
    print("FAISS score of the first chunk in rerank:", best_faiss_score)
    print("Best rerank score:", best_rerank_score)
    print("Average top rerank score:", avg_top_rerank)
    print("Unique sources in top results:", unique_sources)

    if best_rerank_score < 0.15 and avg_top_rerank < 0.08:
        return {
            "fallback_answer": "Yüklenen dokümanlarda bu soruyu net biçimde yanıtlayacak yeterli bilgi bulamadım.",
            "fallback_reason": "insufficient_context",
            "context": "",
            "chunks": [],
            "messages": None,
        }

    context_blocks = []

    for idx, item in enumerate(top_results, start=1):
        doc = item["doc"]
        source = doc.metadata.get("source", "Bilinmeyen kaynak")
        page = doc.metadata.get("page", "Bilinmiyor")
        section_title = doc.metadata.get("section_title", "Bilinmiyor")

        block = (
            f"[KAYNAK {idx}]\n"
            f"Dosya: {source}\n"
            f"Sayfa: {page}\n"
            f"Bölüm: {section_title}\n"
            f"İçerik:\n{doc.page_content}"
        )
        context_blocks.append(block)

    full_context = "\n\n".join(context_blocks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if isinstance(chat_history, list):
        safe_history = []

        for msg in chat_history[-4:]:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = (msg.get("content") or "").strip()
                if role in ["user", "assistant"] and content:
                    safe_history.append({"role": role, "content": content[:2000]})

            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                user_msg = str(msg[0]).strip()
                assistant_msg = str(msg[1]).strip()

                if user_msg:
                    safe_history.append({"role": "user", "content": user_msg[:1000]})
                if assistant_msg:
                    safe_history.append({"role": "assistant", "content": assistant_msg[:1000]})

        messages.extend(safe_history)

    messages.append({
        "role": "user",
        "content": f"""BAĞLAM:
{full_context}

SORU: {user_input}

Lütfen soruyu yalnızca verilen bağlama dayanarak Türkçe cevapla.
Cevap net, profesyonel, doğal ve kullanıcıya doğrudan gösterilecek metin formatında olsun.
BAĞLAM dışında bilgi ekleme, tahmin yapma, yorum katma.
"""
    })

    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    cleaned_chunks = []
    for item in top_results:
        doc = item["doc"]

        cleaned_chunks.append({
            "chunk_id": doc.metadata.get("chunk_id"),
            "page": doc.metadata.get("page"),
            "source": doc.metadata.get("source"),
            "section_title": doc.metadata.get("section_title", "Bilinmiyor"),
            "faiss_score": item["faiss_score"],
            "rerank_score": item["rerank_score"],
            "used_query": item.get("used_query"),
            "chunk_text": doc.page_content
        })

    return {
        "fallback_answer": None,
        "fallback_reason": None,
        "context": full_context,
        "chunks": cleaned_chunks,
        "messages": messages,
        "formatted_prompt": formatted,
    }


# -------------------------------------------------
# 5️⃣ NORMAL RAG
# -------------------------------------------------

def run_rag(user_input: str, chat_history=None):
    payload = build_rag_payload(user_input, chat_history)

    if payload["fallback_answer"] is not None:
        return {
            "answer": payload["fallback_answer"],
            "context": payload["context"],
            "chunks": payload["chunks"],
            "is_fallback": True,
            "fallback_reason": payload.get("fallback_reason")
        }

    model_inputs = tokenizer([payload["formatted_prompt"]], return_tensors="pt").to(DEVICE)

    generated_ids = model.generate(
        model_inputs.input_ids,
        attention_mask=model_inputs.attention_mask,
        eos_token_id=tokenizer.eos_token_id,
        **GENERATION_KWARGS
    )

    response_text = tokenizer.decode(
        generated_ids[0][len(model_inputs.input_ids[0]):],
        skip_special_tokens=True
    ).strip()

    return {
        "answer": response_text,
        "context": payload["context"],
        "chunks": payload["chunks"],
        "is_fallback": False,
        "fallback_reason": None
    }


# -------------------------------------------------
# 6️⃣ STREAMING RAG
# -------------------------------------------------

def build_context_payload(
    user_input: str,
    context: str,
    chat_history=None,
    context_title: str = "KİŞİSEL ÇALIŞAN BİLGİSİ"
):
    if chat_history is None:
        chat_history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if isinstance(chat_history, list):
        safe_history = []

        for msg in chat_history[-4:]:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = (msg.get("content") or "").strip()

                if role in ["user", "assistant"] and content:
                    safe_history.append({
                        "role": role,
                        "content": content[:2000]
                    })

            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                user_msg = str(msg[0]).strip()
                assistant_msg = str(msg[1]).strip()

                if user_msg:
                    safe_history.append({
                        "role": "user",
                        "content": user_msg[:1000]
                    })

                if assistant_msg:
                    safe_history.append({
                        "role": "assistant",
                        "content": assistant_msg[:1000]
                    })

        messages.extend(safe_history)

    messages.append({
        "role": "user",
        "content": f"""{context_title}:
{context}

SORU: {user_input}

Lütfen soruyu yalnızca verilen kişisel çalışan bilgisine dayanarak Türkçe cevapla.
Cevap net, profesyonel, doğal ve kullanıcıya doğrudan gösterilecek metin formatında olsun.
Verilen bağlamda olmayan bilgileri uydurma.
Eğer cevap için yeterli bilgi yoksa, bunu açıkça belirt.
"""
    })

    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    return {
        "context": context,
        "messages": messages,
        "formatted_prompt": formatted
    }


def run_context_stream(
    user_input: str,
    context: str,
    chat_history=None,
    context_title: str = "KİŞİSEL ÇALIŞAN BİLGİSİ"
):
    payload = build_context_payload(
        user_input=user_input,
        context=context,
        chat_history=chat_history,
        context_title=context_title
    )

    model_inputs = tokenizer(
        [payload["formatted_prompt"]],
        return_tensors="pt"
    ).to(DEVICE)

    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )

    generation_kwargs = {
        "input_ids": model_inputs.input_ids,
        "attention_mask": model_inputs.attention_mask,
        "eos_token_id": tokenizer.eos_token_id,
        "streamer": streamer,
        **GENERATION_KWARGS
    }

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    def token_generator():
        for piece in streamer:
            if piece:
                yield piece

    return token_generator(), payload


def build_hybrid_payload(
    user_input: str,
    personal_context: str,
    chat_history=None
):
    if chat_history is None:
        chat_history = []

    rag_payload = build_rag_payload(user_input, chat_history)

    document_context = rag_payload.get("context") or ""
    rag_fallback_answer = rag_payload.get("fallback_answer")
    rag_fallback_reason = rag_payload.get("fallback_reason")
    chunks = rag_payload.get("chunks", [])

    if not document_context:
        document_context = (
            "Bu soru için yüklenen dokümanlardan uygun bir bağlam bulunamadı."
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if isinstance(chat_history, list):
        safe_history = []

        for msg in chat_history[-4:]:
            if isinstance(msg, dict):
                role = msg.get("role")
                content = (msg.get("content") or "").strip()

                if role in ["user", "assistant"] and content:
                    safe_history.append({
                        "role": role,
                        "content": content[:2000]
                    })

            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                user_msg = str(msg[0]).strip()
                assistant_msg = str(msg[1]).strip()

                if user_msg:
                    safe_history.append({
                        "role": "user",
                        "content": user_msg[:1000]
                    })

                if assistant_msg:
                    safe_history.append({
                        "role": "assistant",
                        "content": assistant_msg[:1000]
                    })

        messages.extend(safe_history)

    messages.append({
        "role": "user",
        "content": f"""KİŞİSEL ÇALIŞAN BİLGİSİ:
{personal_context}

DOKÜMAN BAĞLAMI:
{document_context}

SORU: {user_input}

Lütfen soruyu yalnızca yukarıdaki kişisel çalışan bilgisi ve doküman bağlamına dayanarak Türkçe cevapla.

Kurallar:
- Kişisel bilgi gerekiyorsa sadece KİŞİSEL ÇALIŞAN BİLGİSİ bölümündeki verileri kullan.
- Politika, prosedür veya genel HR kuralı gerekiyorsa sadece DOKÜMAN BAĞLAMI bölümündeki bilgileri kullan.
- Verilen bağlamlarda olmayan bilgileri uydurma.
- Eğer gerekli bilgi bağlamda yoksa bunu açıkça belirt.
- Cevap net, profesyonel, doğal ve kullanıcıya doğrudan gösterilecek formatta olsun.
"""
    })

    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    return {
        "personal_context": personal_context,
        "document_context": document_context,
        "chunks": chunks,
        "messages": messages,
        "formatted_prompt": formatted,
        "rag_fallback_answer": rag_fallback_answer,
        "rag_fallback_reason": rag_fallback_reason
    }


def run_hybrid_stream(
    user_input: str,
    personal_context: str,
    chat_history=None
):
    payload = build_hybrid_payload(
        user_input=user_input,
        personal_context=personal_context,
        chat_history=chat_history
    )

    model_inputs = tokenizer(
        [payload["formatted_prompt"]],
        return_tensors="pt"
    ).to(DEVICE)

    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )

    generation_kwargs = {
        "input_ids": model_inputs.input_ids,
        "attention_mask": model_inputs.attention_mask,
        "eos_token_id": tokenizer.eos_token_id,
        "streamer": streamer,
        **GENERATION_KWARGS
    }

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    def token_generator():
        for piece in streamer:
            if piece:
                yield piece

    return token_generator(), payload


def run_rag_stream(user_input: str, chat_history=None):
    payload = build_rag_payload(user_input, chat_history)

    if payload["fallback_answer"] is not None:
        def fallback_generator():
            yield payload["fallback_answer"]

        return fallback_generator(), payload

    model_inputs = tokenizer([payload["formatted_prompt"]], return_tensors="pt").to(DEVICE)

    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )

    generation_kwargs = {
        "input_ids": model_inputs.input_ids,
        "attention_mask": model_inputs.attention_mask,
        "eos_token_id": tokenizer.eos_token_id,
        "streamer": streamer,
        **GENERATION_KWARGS
    }

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    def token_generator():
        for piece in streamer:
            if piece:
                yield piece

    return token_generator(), payload