import re

ARABIC_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

URL_REGEX = re.compile(
    r"(?:https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|telegram\.dog/\S+|wa\.me/\S+|chat\.whatsapp\.com/\S+|api\.whatsapp\.com/\S+|bit\.ly/\S+|tinyurl\.com/\S+|cutt\.ly/\S+|shorturl\.at/\S+)",
    re.IGNORECASE,
)

USERNAME_REGEX = re.compile(r"(?<!\w)@[A-Za-z0-9_]{4,}", re.IGNORECASE)
PHONE_REGEX = re.compile(r"(?:(?:\+|00)?\d[\d\s\-\(\)]{7,}\d)", re.IGNORECASE)
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", re.UNICODE)
SPACE_REGEX = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = (text or "").translate(ARABIC_DIGIT_MAP).lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = text.replace("ـ", "")
    text = PUNCTUATION_REGEX.sub(" ", text)
    text = SPACE_REGEX.sub(" ", text).strip()
    return text


def contains_any_phrase(normalized_text: str, phrases: list[str]) -> str | None:
    for phrase in phrases:
        normalized_phrase = normalize_text(phrase)
        if normalized_phrase and normalized_phrase in normalized_text:
            return phrase
    return None


def contains_link(text: str, additional_patterns: list[str] | None = None) -> bool:
    raw = (text or "").lower()
    if URL_REGEX.search(raw):
        return True
    if USERNAME_REGEX.search(raw):
        return True
    if additional_patterns:
        return any(pattern.lower() in raw for pattern in additional_patterns)
    return False


def contains_phone_number(text: str) -> bool:
    raw = (text or "").translate(ARABIC_DIGIT_MAP)
    match = PHONE_REGEX.search(raw)
    if not match:
        return False

    digits_only = re.sub(r"\D", "", match.group(0))
    return len(digits_only) >= 8
