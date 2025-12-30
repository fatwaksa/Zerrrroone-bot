import logging
import requests
import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import os
import asyncio

# =========================
# الإعدادات
# =========================
TOKEN = os.getenv("BOT_TOKEN")  # تأكد من وضع التوكن في متغير البيئة على Railway

PROXY_API = "https://api.codetabs.com/v1/proxy/?quest="

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html"
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# أوامر البوت
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في **ZeroOne!**\n\n"
        "📥 أرسل *اسم مستخدم سناب شات* لاستخراج القصص العامة.\n\n"
        "مثال:\n"
        "`snapchat`\n\n"
        "⚠️ القصص الخاصة غير مدعومة.",
        parse_mode="Markdown"
    )

# =========================
# منطق استخراج سناب
# =========================
def extract_snaps(username: str):
    url = f"https://story.snapchat.com/@{username}"
    proxy_url = PROXY_API + url

    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        logging.error(f"Error fetching URL: {e}")
        return []

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
        html
    )

    if not match:
        return []

    try:
        data = json.loads(match.group(1))
        snaps = (
            data.get("props", {})
            .get("pageProps", {})
            .get("story", {})
            .get("snapList", [])
        )
    except Exception as e:
        logging.error(f"Error parsing JSON: {e}")
        return []

    results = []
    for snap in snaps:
        urls = snap.get("snapUrls", {})
        media = urls.get("mediaUrl") or urls.get("mediaManifestUrl")
        if media:
            results.append(media)

    return results

# =========================
# استقبال اسم المستخدم
# =========================
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")

    msg = await update.message.reply_text("⏳ جاري استخراج القصص...")

    try:
        snaps = extract_snaps(username)

        if not snaps:
            await msg.edit_text(
                f"❌ لا توجد قصص عامة أو الحساب غير موجود.\n\n"
                f"🔗 https://story.snapchat.com/@{username}"
            )
            return

        await msg.edit_text(f"✅ تم العثور على {len(snaps)} عنصر")

        for i, media_url in enumerate(snaps, start=1):
            is_video = ".mp4" in media_url or "render" in media_url

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬇️ تحميل مباشر",
                        url=media_url
                    )
                ]
            ])

            caption = f"📦 ZeroOne\n👤 @{username}\n#{i}"

            try:
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
            except Exception as e:
                logging.warning(f"Failed to send media: {e}")

    except Exception as e:
        logging.error(f"Error in handle_username: {e}")
        await msg.edit_text(
            "⚠️ حدث خطأ أو تم حظر الاتصال.\n\n"
            f"🔗 https://story.snapchat.com/@{username}"
        )

# =========================
# تشغيل البوت
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))

    print("🤖 ZeroOne Telegram Bot is running...")
    app.run_polling(poll_interval=2.0, timeout=10, allowed_updates=None)

if __name__ == "__main__":
    main()
ة
