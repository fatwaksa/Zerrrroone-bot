import os
import re
import json
import asyncio
import logging
import aiohttp

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

# =========================
# الإعدادات العامة
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # 🔒 أمان البوت
PROXY_API = "https://api.codetabs.com/v1/proxy/?quest="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (SnapBot)",
    "Accept": "text/html"
}

TIMEOUT = aiohttp.ClientTimeout(total=20)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("ZeroOne")

# =========================
# أدوات مساعدة
# =========================

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._]{3,30}$")

def valid_username(username: str) -> bool:
    """يتأكد أن اسم المستخدم صالح"""
    return bool(USERNAME_REGEX.match(username))


async def fetch_html(url: str) -> str | None:
    """جلب صفحة HTML باستخدام aiohttp"""
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    return None
                return await response.text()
    except Exception as e:
        logger.warning(f"فشل تحميل الصفحة: {e}")
        return None


# =========================
# استخراج القصص
# =========================

async def extract_snaps(username: str) -> list[str]:
    """يستخرج روابط القصص العامة من سناب شات"""
    target_url = f"https://story.snapchat.com/@{username}"
    proxy_url = PROXY_API + target_url

    html = await fetch_html(proxy_url)
    if not html:
        return []

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">\s*(\{.*?\})\s*</script>',
        html,
        re.DOTALL
    )

    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    snaps = (
        data.get("props", {})
        .get("pageProps", {})
        .get("story", {})
        .get("snapList", [])
    )

    results = []
    for snap in snaps:
        urls = snap.get("snapUrls", {})
        media = urls.get("mediaUrl") or urls.get("mediaManifestUrl")
        if media:
            results.append(media)

    return results


# =========================
# أوامر البوت
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة ترحيب شخصية"""
    user_first_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(
        f"👋 أهلاً بك {user_first_name} في **بوت زيرو ون!**\n\n"
        "📥 أرسل *اسم مستخدم سناب شات* لاستخراج **القصص العامة فقط**\n\n"
        "⚠️ القصص الخاصة غير مدعومة\n\n"
        "المطور: عبدالعزيز الرويلي\n"
        "حساباتي للتواصل: https://bio-link.se/em2cc",
        parse_mode="Markdown"
    )


# =========================
# استقبال اسم المستخدم
# =========================

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم المستخدم واستخراج القصص"""
    raw = update.message.text.strip()
    username = raw.replace("@", "")

    if not valid_username(username):
        await update.message.reply_text("❌ اسم المستخدم غير صالح")
        return

    status = await update.message.reply_text("⏳ جاري استخراج القصص...")

    try:
        snaps = await extract_snaps(username)

        if not snaps:
            await status.edit_text(
                "❌ لا توجد قصص عامة أو الحساب غير متاح\n\n"
                f"🔗 https://story.snapchat.com/@{username}"
            )
            return

        await status.edit_text(f"✅ تم العثور على {len(snaps)} قصة")

        for i, media_url in enumerate(snaps, start=1):
            is_video = any(x in media_url for x in (".mp4", "render", "manifest"))

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬇️ تحميل مباشر", url=media_url)]
            ])

            caption = f"📦 زيرو ون\n👤 @{username}\n#{i}"

            if is_video:
                await update.message.reply_video(
                    video=media_url,
                    caption=caption,
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_photo(
                    photo=media_url,
                    caption=caption,
                    reply_markup=keyboard
                )

            await asyncio.sleep(0.4)  # لمنع الحظر

    except Exception as e:
        logger.exception("⚠️ حدث خطأ أثناء استخراج القصص")
        await status.edit_text("⚠️ حدث خطأ غير متوقع")


# =========================
# تشغيل البوت
# =========================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN غير موجود في متغيرات البيئة")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))

    logger.info("🤖 بوت زيرو ون يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
