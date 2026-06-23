from threading import Lock
from transformers import pipeline


MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

print(f"Shared classifier loading ({MODEL_ID})...")

zero_shot_classifier = pipeline(
    task="zero-shot-classification",
    model=MODEL_ID,
    device=-1
)

classifier_lock = Lock()


def run_zero_shot_classification(
    text: str,
    candidate_labels: list[str],
    hypothesis_template: str
):
    """
    Kategori ve scope sınıflandırıcılarının aynı modeli güvenli şekilde
    kullanmasını sağlar.
    """

    cleaned_text = (text or "").strip()

    if not cleaned_text:
        raise ValueError("Sınıflandırılacak metin boş olamaz.")

    if not candidate_labels:
        raise ValueError("Candidate label listesi boş olamaz.")

    with classifier_lock:
        return zero_shot_classifier(
            cleaned_text,
            candidate_labels=candidate_labels,
            hypothesis_template=hypothesis_template,
            multi_label=False
        )