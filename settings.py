import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
MODERATION_ENABLED = env_bool("MODERATION_ENABLED", True)
BLOCK_LINKS = env_bool("BLOCK_LINKS", True)
BLOCK_PHONE_NUMBERS = env_bool("BLOCK_PHONE_NUMBERS", True)
SEND_ALERT_MESSAGES = env_bool("SEND_ALERT_MESSAGES", True)
ALERT_MESSAGE_AUTO_DELETE_SECONDS = env_int("ALERT_MESSAGE_AUTO_DELETE_SECONDS", 8)
ABUSE_BAN_THRESHOLD = env_int("ABUSE_BAN_THRESHOLD", 0)
DROP_PENDING_UPDATES = env_bool("DROP_PENDING_UPDATES", True)
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))
READ_TIMEOUT = env_int("READ_TIMEOUT", 30)
WRITE_TIMEOUT = env_int("WRITE_TIMEOUT", 30)
CONNECT_TIMEOUT = env_int("CONNECT_TIMEOUT", 30)
POOL_TIMEOUT = env_int("POOL_TIMEOUT", 30)

SAFE_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("SAFE_USER_IDS", "").split(",")
    if user_id.strip().isdigit()
}

# أنماط تعتبر وسيلة تواصل/رابط ويؤدي وجودها إلى حذف الرسالة وحظر المرسل.
USERNAME_LINK_PATTERNS = [
    "http://",
    "https://",
    "www.",
    "t.me/",
    "telegram.me/",
    "telegram.dog/",
    "wa.me/",
    "chat.whatsapp.com/",
    "api.whatsapp.com/",
    "bit.ly/",
    "tinyurl.com/",
    "goo.gl/",
    "cutt.ly/",
    "shorturl.at/",
]

# عبارات إعلانية طلبتَ حظرها.
BANNED_AD_PHRASES = [
    "♨️حل واجبات او بحوث او عروض ومشاريع وحتى حلول الكويزات والاختبارات",
    "حل واجبات او بحوث او عروض ومشاريع وحتى حلول الكويزات والاختبارات",
    "....حلولهم ثقة ومضمونة ولديهم تجارب العديد من الطلاب والطالبات",
    "حلولهم ثقة ومضمونة ولديهم تجارب العديد من الطلاب والطالبات",
    "حل واجبات",
    "حل بحوث",
    "حلولهم ثقة ومضمونة",
    "لديهم تجارب العديد من الطلاب والطالبات",
    "للتواصل واتساب",
    "تعال خاص",
    "للتواصل",
    "خصم",
    "خدمات طلابية",
    "سكليف",
    "مساعدة",
    "خش خاص",
    "خاص",
    "خدمات طلابية",
"حل واجبات",
"حل الواجبات",
"حل اختبارات",
"حل الاختبارات",
"حل كويز",
"اسايمنتات",
"لابات",
"واجبات",
"أنشطة",
"تكاليف",
"بحوث",
"بحوثات",
"أبحاث",
"رسائل ماجستير",
"رسائل دكتوراه",
"اعداد بحوث",
"اعداد تقارير",
"اعداد مشاريع",
"مشاريع تخرج",
"تلخيص كتب",
"تلخيص محاضرات",
"تفريغ محاضرات",
"ترجمة كتب",
"ترجمة محاضرات",
"كتابة مقالات",
"تصميم cv",
"تحليل استبيان",
"مشاريع البرمجة",
"حل البرمجة",
"مشروع برمجي",
"سكليف",
"اجازة مرضية",
"إجازة مرضية",
"اعذار طبية",
"أعذار طبية",
"تقرير طبي",
"شهادة صحية",
"كشف طبي",
"للتواصل خاص",
"للتواصل واتساب",
"تواصل واتس",
"واتساب",
"whatsapp",
"wa.me",
"chat.whatsapp",
"اسعار رمزية",
"فريق متخصص",
"كادر متخصص",
"جميع التخصصات",
"بأفضل الأسعار",
"+967",
"+966",
"00966",
"00967",
]

# أضف هنا الكلمات المسيئة التي تريد حذفها. افتراضيًا القائمة فارغة لتجنب الحظر الخاطئ.
CUSTOM_BANNED_ABUSE_TERMS = [
    # مثال: "كلمة مسيئة",
]


def _normalized_unique(items: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for item in items:
        value = " ".join(item.split()).strip().lower()
        if value and value not in seen:
            cleaned.append(value)
            seen.add(value)
    return cleaned


def build_banned_ad_phrases() -> list[str]:
    return _normalized_unique(BANNED_AD_PHRASES)


def build_banned_abuse_terms() -> list[str]:
    return _normalized_unique(CUSTOM_BANNED_ABUSE_TERMS)
