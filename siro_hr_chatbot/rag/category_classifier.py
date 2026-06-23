import re

from .classifier_runtime import run_zero_shot_classification


# -------------------------------------------------
# 1. CATEGORY DEFINITIONS
# -------------------------------------------------

CATEGORY_LABELS = {
    "leaves": "izinler",
    "benefits": "yan haklar",
    "payroll": "maaş ve bordro",
    "performance": "performans değerlendirme",
    "recruitment": "işe alım",
    "training": "eğitim",
    "discipline": "disiplin süreçleri",
    "health_safety": "iş sağlığı ve güvenliği",
    "company_policies": "şirket politikaları",
    "other": "diğer"
}

LABEL_TO_KEY = {
    label: key
    for key, label in CATEGORY_LABELS.items()
}


# -------------------------------------------------
# 2. CLASSIFICATION THRESHOLDS
# -------------------------------------------------

MIN_CATEGORY_SCORE = 0.30
MIN_CATEGORY_MARGIN = 0.05


# -------------------------------------------------
# 3. KEYWORD RULES
# -------------------------------------------------

KEYWORD_CATEGORY_RULES = {
    "payroll": [
        "maaş",
        "maas",
        "maaşım",
        "maasim",
        "ücret",
        "ucret",
        "bordro",
        "bordrom",
        "prim",
        "primim",
        "zam",
        "ödeme",
        "odeme",
        "kesinti",
        "net maaş",
        "net maas",
        "brüt maaş",
        "brut maas",
        "maaş ödemesi",
        "maas odemesi"
    ],

    "discipline": [
        "disiplin",
        "hakaret",
        "yaptırım",
        "yaptirim",
        "ceza",
        "uyarı",
        "uyari",
        "kavga",
        "etik ihlal",
        "ihlal",
        "tutanak",
        "savunma",
        "disiplin cezası",
        "disiplin cezasi"
    ],

    "leaves": [
        "izin",
        "iznim",
        "izinler",
        "izin bakiyesi",
        "izin bakiyem",
        "kalan iznim",
        "yıllık izin",
        "yillik izin",
        "doğum izni",
        "dogum izni",
        "mazeret izni",
        "hastalık izni",
        "hastalik izni",
        "ücretsiz izin",
        "ucretsiz izin",
        "rapor izni",
        "kaç gün iznim kaldı",
        "kac gun iznim kaldi"
    ],

    "benefits": [
        "yan hak",
        "yan haklar",
        "servis",
        "yemek",
        "sigorta",
        "özel sağlık sigortası",
        "ozel saglik sigortasi",
        "sosyal hak",
        "sosyal haklar",
        "ticket",
        "yemek kartı",
        "yemek karti",
        "özel sigorta",
        "ozel sigorta"
    ],

    "performance": [
        "performans",
        "performansım",
        "performansim",
        "hedef",
        "hedeflerim",
        "değerlendirme",
        "degerlendirme",
        "geri bildirim",
        "feedback",
        "terfi",
        "kariyer",
        "performans puanı",
        "performans puanim"
    ],

    "recruitment": [
        "işe alım",
        "ise alim",
        "başvuru",
        "basvuru",
        "mülakat",
        "mulakat",
        "aday",
        "iş ilanı",
        "is ilani",
        "oryantasyon",
        "iş başvurusu",
        "is basvurusu"
    ],

    "training": [
        "eğitim",
        "egitim",
        "kurs",
        "sertifika",
        "gelişim",
        "gelisim",
        "zorunlu eğitim",
        "zorunlu egitim",
        "eğitim programı",
        "egitim programi"
    ],

    "health_safety": [
        "iş sağlığı",
        "is sagligi",
        "iş güvenliği",
        "is guvenligi",
        "iş kazası",
        "is kazasi",
        "kaza",
        "revir",
        "sağlık raporu",
        "saglik raporu",
        "güvenlik",
        "guvenlik",
        "iş güvenliği eğitimi",
        "is guvenligi egitimi"
    ],

    "company_policies": [
        "politika",
        "prosedür",
        "prosedur",
        "şirket kuralı",
        "sirket kurali",
        "şirket kuralları",
        "sirket kurallari",
        "kurallar",
        "çalışma saatleri",
        "calisma saatleri",
        "uzaktan çalışma",
        "uzaktan calisma",
        "hibrit çalışma",
        "hibrit calisma",
        "hibrit",
        "ofis",
        "mesai saatleri"
    ]
}


# -------------------------------------------------
# 4. TEXT HELPERS
# -------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Metni küçük harfe çevirir ve gereksiz boşlukları temizler.
    """

    normalized = (text or "").casefold().strip()
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def contains_keyword(text: str, keyword: str) -> bool:
    """
    Keyword'ün başka bir kelimenin içinde yanlışlıkla eşleşmesini engeller.

    Örnek:
    'ben' kelimesi 'bence' içerisinde eşleşmez.
    """

    normalized_keyword = normalize_text(keyword)

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"

    return re.search(pattern, text) is not None


# -------------------------------------------------
# 5. KEYWORD CLASSIFICATION
# -------------------------------------------------

def keyword_classify(question: str):
    normalized_question = normalize_text(question)

    if not normalized_question:
        return None

    category_scores = {}
    matched_keywords = {}

    for category_key, keywords in KEYWORD_CATEGORY_RULES.items():
        score = 0
        category_matches = []

        for keyword in keywords:
            if contains_keyword(normalized_question, keyword):
                category_matches.append(keyword)

                # Birden fazla kelimeden oluşan ifadeler daha güçlü sinyal.
                if " " in keyword.strip():
                    score += 2
                else:
                    score += 1

        if score > 0:
            category_scores[category_key] = score
            matched_keywords[category_key] = category_matches

    if not category_scores:
        return None

    max_score = max(category_scores.values())

    best_categories = [
        category_key
        for category_key, score in category_scores.items()
        if score == max_score
    ]

    # Tek bir kategori açık şekilde öndeyse keyword sonucu kullanılır.
    if len(best_categories) == 1:
        category_key = best_categories[0]

        return {
            "category_key": category_key,
            "category_name": CATEGORY_LABELS[category_key],
            "score": 1.0,
            "method": "keyword",
            "keyword_scores": category_scores,
            "matched_keywords": matched_keywords.get(category_key, [])
        }

    # Birden fazla kategori aynı skoru aldıysa zero-shot modele bırakılır.
    return None


# -------------------------------------------------
# 6. ZERO-SHOT CLASSIFICATION
# -------------------------------------------------

def zero_shot_classify(question: str):
    """
    Keyword sonucu bulunamadığında zero-shot sınıflandırma yapar.

    'other' kategorisi modele candidate label olarak verilmez.
    Model kararsızsa kod tarafından 'other' atanır.
    """

    candidate_labels = [
        category_name
        for category_key, category_name in CATEGORY_LABELS.items()
        if category_key != "other"
    ]

    result = run_zero_shot_classification(
        text=question,
        candidate_labels=candidate_labels,
        hypothesis_template="Bu soru {} konusu ile ilgilidir."
    )

    top_label = result["labels"][0]
    top_score = float(result["scores"][0])

    second_score = (
        float(result["scores"][1])
        if len(result["scores"]) > 1
        else 0.0
    )

    score_margin = top_score - second_score
    category_key = LABEL_TO_KEY.get(top_label)

    low_confidence = (
        category_key is None
        or top_score < MIN_CATEGORY_SCORE
        or score_margin < MIN_CATEGORY_MARGIN
    )

    if low_confidence:
        return {
            "category_key": "other",
            "category_name": CATEGORY_LABELS["other"],
            "score": top_score,
            "score_margin": score_margin,
            "method": "zero_shot_low_confidence",
            "all_labels": result["labels"],
            "all_scores": [
                float(score)
                for score in result["scores"]
            ]
        }

    return {
        "category_key": category_key,
        "category_name": CATEGORY_LABELS[category_key],
        "score": top_score,
        "score_margin": score_margin,
        "method": "zero_shot",
        "all_labels": result["labels"],
        "all_scores": [
            float(score)
            for score in result["scores"]
        ]
    }


# -------------------------------------------------
# 7. MAIN CLASSIFICATION FUNCTION
# -------------------------------------------------

def classify_question_category(question: str):
    cleaned_question = (question or "").strip()

    if not cleaned_question:
        return {
            "category_key": "other",
            "category_name": CATEGORY_LABELS["other"],
            "score": 0.0,
            "score_margin": 0.0,
            "method": "empty_question"
        }

    keyword_result = keyword_classify(cleaned_question)

    if keyword_result is not None:
        return keyword_result

    try:
        return zero_shot_classify(cleaned_question)

    except Exception as error:
        print(
            f"[CATEGORY CLASSIFICATION ERROR] "
            f"question='{cleaned_question}' error={error}"
        )

        # Classification hatası durumunda güvenli varsayılan.
        return {
            "category_key": "other",
            "category_name": CATEGORY_LABELS["other"],
            "score": 0.0,
            "score_margin": 0.0,
            "method": "classification_error",
            "error": str(error)
        }