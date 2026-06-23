import re

from .classifier_runtime import run_zero_shot_classification


# -------------------------------------------------
# 1. SCOPE DEFINITIONS
# -------------------------------------------------

SCOPE_LABELS = {
    "general": "şirket politikalarıyla ilgili genel bilgi",
    "personal": "çalışanın kişisel kayıtlarıyla ilgili bilgi",
    "hybrid": "kişisel kayıtlar ve şirket politikalarını birlikte gerektiren bilgi"
}

LABEL_TO_KEY = {
    label: key
    for key, label in SCOPE_LABELS.items()
}


# -------------------------------------------------
# 2. CLASSIFICATION THRESHOLDS
# -------------------------------------------------

MIN_SCOPE_SCORE = 0.45
MIN_SCOPE_MARGIN = 0.08


# -------------------------------------------------
# 3. KEYWORD RULES
# -------------------------------------------------
GENERAL_INFORMATION_KEYWORDS = [
    "hakkında bilgi",
    "bilgi verir misin",
    "nedir",
    "ne demek",
    "nasıl işler",
    "nasıl uygulanır",
    "kaç gündür",
    "süresi nedir",
    "şartları nelerdir",
    "koşulları nelerdir",
    "politikası nedir",
    "prosedürü nedir",
    "kimler yararlanabilir",
    "genel bilgi"
]
PERSONAL_KEYWORDS = [
    "benim",
    "bana",
    "ben",
    "kendim",
    "kendi",
    "bana özel",
    "benim için",

    "maaşım",
    "maasim",
    "bordrom",
    "primim",
    "ücretim",
    "ucretim",

    "izin bakiyem",
    "kalan iznim",
    "iznim",
    "kaç gün iznim kaldı",
    "kac gun iznim kaldi",

    "performansım",
    "performansim",
    "performans puanım",
    "performans puanim",

    "departmanım",
    "departmanim",
    "yöneticim",
    "yoneticim",

    "çalışan numaram",
    "calisan numaram",
    "sicilim",
    "özlük bilgilerim",
    "ozluk bilgilerim"
]

HYBRID_HINTS = [
    "benim durumumda",
    "durumuma göre",
    "durumuma gore",
    "buna göre",
    "buna gore",

    "kalan iznime göre",
    "kalan iznime gore",
    "maaşıma göre",
    "maasima gore",
    "performansıma göre",
    "performansima gore",

    "hak kazanır mıyım",
    "hak kazanir miyim",
    "yararlanabilir miyim",
    "uygun muyum",

    "kaç gün kullanabilirim",
    "kac gun kullanabilirim",
    "ne kadar kullanabilirim"
]


# -------------------------------------------------
# 4. TEXT HELPERS
# -------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Metni normalize eder ve gereksiz boşlukları temizler.
    """

    normalized = (text or "").casefold().strip()
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def contains_keyword(text: str, keyword: str) -> bool:
    """
    Keyword'ün başka kelimelerin içerisinde yanlış eşleşmesini engeller.
    """

    normalized_keyword = normalize_text(keyword)

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"

    return re.search(pattern, text) is not None


# -------------------------------------------------
# 5. KEYWORD CLASSIFICATION
# -------------------------------------------------

def keyword_scope_classify(question: str):
    normalized_question = normalize_text(question)

    if not normalized_question:
        return None

    personal_matches = []
    hybrid_matches = []
    general_matches = []

    for keyword in PERSONAL_KEYWORDS:
        if contains_keyword(normalized_question, keyword):
            personal_matches.append(keyword)

    for keyword in HYBRID_HINTS:
        if contains_keyword(normalized_question, keyword):
            hybrid_matches.append(keyword)

    for keyword in GENERAL_INFORMATION_KEYWORDS:
        if contains_keyword(normalized_question, keyword):
            general_matches.append(keyword)

    if personal_matches and hybrid_matches:
        return {
            "scope": "hybrid",
            "score": 1.0,
            "method": "keyword",
            "personal_matches": personal_matches,
            "hybrid_matches": hybrid_matches,
            "general_matches": general_matches
        }
    
    if personal_matches:
        return {
            "scope": "personal",
            "score": 1.0,
            "method": "keyword",
            "personal_matches": personal_matches,
            "hybrid_matches": [],
            "general_matches": general_matches
        }
    
    if general_matches:
        return {
            "scope": "general",
            "score": 1.0,
            "method": "keyword",
            "personal_matches": [],
            "hybrid_matches": [],
            "general_matches": general_matches
        }


    return None



def has_explicit_personal_signal(question: str) -> bool:
    normalized_question = normalize_text(question)

    return any(
        contains_keyword(normalized_question, keyword)
        for keyword in PERSONAL_KEYWORDS
    )
# -------------------------------------------------
# 6. ZERO-SHOT CLASSIFICATION
# -------------------------------------------------

def zero_shot_scope_classify(question: str):
    candidate_labels = list(SCOPE_LABELS.values())

    result = run_zero_shot_classification(
        text=question,
        candidate_labels=candidate_labels,
        hypothesis_template="Bu soru {} gerektirir."
    )

    top_label = result["labels"][0]
    top_score = float(result["scores"][0])

    second_score = (
        float(result["scores"][1])
        if len(result["scores"]) > 1
        else 0.0
    )

    score_margin = top_score - second_score
    scope_key = LABEL_TO_KEY.get(top_label, "general")
    
    personal_signal = has_explicit_personal_signal(question)

    if scope_key in ["personal", "hybrid"] and not personal_signal:
        return {
            "scope": "general",
            "score": top_score,
            "score_margin": score_margin,
            "method": "model_personal_rejected",
            "predicted_scope": scope_key,
            "all_labels": result["labels"],
            "all_scores": [
                float(score)
                for score in result["scores"]
            ]
        }


    low_confidence = (
        top_score < MIN_SCOPE_SCORE
        or score_margin < MIN_SCOPE_MARGIN
    )

    # Model kararsızsa kişisel API çağrısı yapılmaması için
    # güvenli varsayılan olarak general seçilir.
    if low_confidence:
        return {
            "scope": "general",
            "score": top_score,
            "score_margin": score_margin,
            "method": "model_low_confidence",
            "predicted_scope": scope_key,
            "all_labels": result["labels"],
            "all_scores": [
                float(score)
                for score in result["scores"]
            ]
        }

    return {
        "scope": scope_key,
        "score": top_score,
        "score_margin": score_margin,
        "method": "model",
        "all_labels": result["labels"],
        "all_scores": [
            float(score)
            for score in result["scores"]
        ]
    }


# -------------------------------------------------
# 7. MAIN CLASSIFICATION FUNCTION
# -------------------------------------------------

def classify_question_scope(question: str):
    cleaned_question = (question or "").strip()

    if not cleaned_question:
        return {
            "scope": "general",
            "score": 0.0,
            "score_margin": 0.0,
            "method": "empty_question"
        }

    keyword_result = keyword_scope_classify(cleaned_question)

    if keyword_result is not None:
        return keyword_result

    try:
        return zero_shot_scope_classify(cleaned_question)

    except Exception as error:
        print(
            f"[SCOPE CLASSIFICATION ERROR] "
            f"question='{cleaned_question}' error={error}"
        )

        # Hata durumunda kişisel API'ye yanlış yönlendirme yapılmaması için
        # general route seçilir.
        return {
            "scope": "general",
            "score": 0.0,
            "score_margin": 0.0,
            "method": "classification_error",
            "error": str(error)
        }