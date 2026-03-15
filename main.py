import asyncio
import logging
from collections import defaultdict

from telegram import Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from settings import (
    ABUSE_BAN_THRESHOLD,
    ALERT_MESSAGE_AUTO_DELETE_SECONDS,
    BLOCK_LINKS,
    BLOCK_PHONE_NUMBERS,
    BOT_TOKEN,
    CONNECT_TIMEOUT,
    DROP_PENDING_UPDATES,
    LOG_LEVEL,
    MODERATION_ENABLED,
    POLL_INTERVAL,
    POOL_TIMEOUT,
    READ_TIMEOUT,
    SAFE_USER_IDS,
    SEND_ALERT_MESSAGES,
    USERNAME_LINK_PATTERNS,
    WRITE_TIMEOUT,
    build_banned_abuse_terms,
    build_banned_ad_phrases,
)
from text_utils import contains_any_phrase, contains_link, contains_phone_number, normalize_text

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)

ad_phrases = build_banned_ad_phrases()
abuse_terms = build_banned_abuse_terms()
abuse_strikes = defaultdict(int)


async def is_protected_user(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    if user.is_bot or user.id in SAFE_USER_IDS:
        return True

    try:
        member = await chat.get_member(user.id)
        return member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    except Exception as exc:
        logger.warning("Failed to check member status for user=%s: %s", user.id, exc)
        return False


async def safe_delete_message(update: Update) -> None:
    message = update.effective_message
    if not message:
        return
    try:
        await message.delete()
    except Exception as exc:
        logger.warning("Failed to delete message: %s", exc)


async def safe_ban_user(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    try:
        await update.get_bot().ban_chat_member(chat_id=chat.id, user_id=user.id)
        return True
    except Exception as exc:
        logger.warning("Failed to ban user=%s in chat=%s: %s", user.id, chat.id, exc)
        return False


async def send_alert(update: Update, text: str) -> None:
    if not SEND_ALERT_MESSAGES:
        return

    chat = update.effective_chat
    if not chat:
        return

    try:
        sent = await chat.send_message(text, parse_mode=ParseMode.HTML)
        if ALERT_MESSAGE_AUTO_DELETE_SECONDS > 0:
            asyncio.create_task(_sleep_and_delete(ALERT_MESSAGE_AUTO_DELETE_SECONDS, sent))
    except Exception as exc:
        logger.warning("Failed to send alert: %s", exc)


async def _sleep_and_delete(seconds: int, sent_message) -> None:
    await asyncio.sleep(seconds)
    try:
        await sent_message.delete()
    except Exception:
        pass


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "البوت يعمل ✅\n"
            "وظيفته حذف الإعلانات والروابط وأرقام الهواتف، مع حظر مرسلي الإعلانات تلقائيًا."
        )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("pong ✅")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "الحالة الحالية:\n"
            f"- الحماية مفعلة: {'نعم' if MODERATION_ENABLED else 'لا'}\n"
            f"- حظر الروابط: {'نعم' if BLOCK_LINKS else 'لا'}\n"
            f"- حظر أرقام الهواتف: {'نعم' if BLOCK_PHONE_NUMBERS else 'لا'}\n"
            f"- حذف التحديثات القديمة عند التشغيل: {'نعم' if DROP_PENDING_UPDATES else 'لا'}\n"
            f"- المستخدمون المستثنون: {len(SAFE_USER_IDS)}\n"
            f"- عدد عبارات الإعلانات: {len(ad_phrases)}\n"
            f"- عدد الكلمات المسيئة: {len(abuse_terms)}"
        )


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not MODERATION_ENABLED:
        return

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return

    if await is_protected_user(update):
        return

    text = message.text or message.caption or ""
    if not text:
        return

    normalized = normalize_text(text)
    reasons = []
    should_ban_for_ad = False

    matched_ad_phrase = contains_any_phrase(normalized, ad_phrases)
    if matched_ad_phrase:
        reasons.append(f"عبارة إعلانية محظورة: {matched_ad_phrase}")
        should_ban_for_ad = True

    if BLOCK_LINKS and contains_link(text, USERNAME_LINK_PATTERNS):
        reasons.append("رابط أو وسيلة تواصل محظورة")
        should_ban_for_ad = True

    if BLOCK_PHONE_NUMBERS and contains_phone_number(text):
        reasons.append("رقم هاتف محظور")
        should_ban_for_ad = True

    matched_abuse = contains_any_phrase(normalized, abuse_terms)
    if matched_abuse:
        reasons.append(f"كلمة مسيئة محظورة: {matched_abuse}")

    if not reasons:
        return

    await safe_delete_message(update)
    logger.info(
        "Deleted message in chat=%s from user=%s (%s), reasons=%s",
        chat.id,
        user.id,
        user.full_name,
        "; ".join(reasons),
    )

    if should_ban_for_ad:
        banned = await safe_ban_user(update)
        if banned:
            await send_alert(update, f"🚫 تم حذف رسالة إعلانية وحظر المستخدم {user.mention_html()}.")
        else:
            await send_alert(update, f"⚠️ تم حذف رسالة مخالفة من {user.mention_html()} لكن فشل الحظر. تأكد من صلاحيات البوت.")
        return

    abuse_strikes[(chat.id, user.id)] += 1
    strikes = abuse_strikes[(chat.id, user.id)]

    if ABUSE_BAN_THRESHOLD > 0 and strikes >= ABUSE_BAN_THRESHOLD:
        banned = await safe_ban_user(update)
        if banned:
            await send_alert(update, f"🚫 تم حظر المستخدم {user.mention_html()} بعد تجاوز حد الكلمات المسيئة.")
        else:
            await send_alert(update, f"⚠️ تم حذف رسالة مسيئة من {user.mention_html()} لكن فشل الحظر. تأكد من صلاحيات البوت.")
    else:
        await send_alert(update, f"🗑️ تم حذف رسالة مسيئة من {user.mention_html()}.")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error: %s", context.error)


def build_application() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Please set it in Railway variables or .env file.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(READ_TIMEOUT)
        .write_timeout(WRITE_TIMEOUT)
        .connect_timeout(CONNECT_TIMEOUT)
        .pool_timeout(POOL_TIMEOUT)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(~filters.COMMAND, moderate_message))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    logger.info(
        "Starting Telegram moderation bot | moderation=%s links=%s phones=%s ad_phrases=%s abuse_terms=%s",
        MODERATION_ENABLED,
        BLOCK_LINKS,
        BLOCK_PHONE_NUMBERS,
        len(ad_phrases),
        len(abuse_terms),
    )
    app = build_application()
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=DROP_PENDING_UPDATES,
        poll_interval=POLL_INTERVAL,
    )


if __name__ == "__main__":
    main()
