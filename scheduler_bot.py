"""
scheduler_bot.py
-----------------
Render.com (yoki har qanday doimiy ishlaydigan server) uchun mo'ljallangan
YAGONA, DOIMIY ishlaydigan skript. Bu skript ichida:

- Kunlik jadval (APScheduler) — belgilangan vaqtlarda avtomatik ishlaydi
- Tasdiqlash tizimi — grammar/vocab/idioms/reading postlari avval SIZGA
  (admin) yuboriladi, ✅/❌ tugmalari orqali tasdiqlaysiz
- Test buyruqlari — istalgan vaqtda /test_vocab kabi buyruqlar bilan
  darhol sinab ko'rishingiz mumkin

O'RNATISH:
    pip install -r requirements.txt

ISHGA TUSHIRISH (Render'da "Start Command" sifatida):
    python scheduler_bot.py

KERAKLI ENVIRONMENT VARIABLES (Render dashboard'ida "Environment" bo'limida):
    TELEGRAM_BOT_TOKEN — BotFather'dan olingan token
    GEMINI_API_KEY     — aistudio.google.com/apikey'dan olingan bepul kalit
    ADMIN_CHAT_ID       — sizning shaxsiy Telegram ID'ingiz (@userinfobot orqali)
    CHANNEL_ID          — @sizning_kanalingiz
"""

import os
import logging
import datetime
import zoneinfo
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from content_generator import (
    generate_grammar_post,
    generate_vocabulary_post,
    generate_idiom_post,
    generate_reading_test,
    generate_daily_greeting,
)
from telegram_sender import post_content, _format_to_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
CHANNEL_ID = os.environ["CHANNEL_ID"]
TIMEZONE = zoneinfo.ZoneInfo("Asia/Tashkent")

# Tasdiqlanishi kutilayotgan postlarni vaqtincha xotirada saqlash uchun
pending_posts: dict[str, dict] = {}
_post_counter = 0

CAPTION_LIMIT = 1024


def _photo_arg(post: dict):
    """
    python-telegram-bot'ga rasm sifatida nima berish kerakligini
    aniqlaydi: agar Gemini orqali bayt (bytes) mavjud bo'lsa — fayl
    sifatida, aks holda Pollinations havolasi (URL) sifatida.
    """
    if "image_bytes" in post:
        return BytesIO(post["image_bytes"])
    return post["image_url"]


async def _send_for_approval(app: Application, post: dict):
    """Generatsiya qilingan post (rasm + matn)ni admin'ga tasdiqlash uchun yuboradi."""
    global _post_counter
    _post_counter += 1
    post_id = str(_post_counter)
    pending_posts[post_id] = post

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Kanalga yuborish", callback_data=f"approve:{post_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"reject:{post_id}"),
        ]
    ])

    header = f"🔔 Yangi {post['type']} posti tayyor (tasdiqlashni kuting):"
    await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=header)

    html_text = _format_to_html(post["text"])
    photo = _photo_arg(post)

    if len(post["text"]) <= CAPTION_LIMIT:
        await app.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo,
            caption=html_text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await app.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo)
        await app.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=html_text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


async def job_grammar(app: Application):
    await _send_for_approval(app, generate_grammar_post())


async def job_vocabulary(app: Application):
    await _send_for_approval(app, generate_vocabulary_post())


async def job_idioms(app: Application):
    await _send_for_approval(app, generate_idiom_post())


async def job_reading(app: Application):
    await _send_for_approval(app, generate_reading_test())


async def job_greeting(app: Application):
    """
    Har kuni ertalab 07:00'da ishlaydi. Boshqa postlardan farqli o'laroq,
    BU TO'G'RIDAN-TO'G'RI kanalga chiqadi (tasdiqlashsiz) — chunki oddiy
    salomlashish xabari xato bo'lish xavfi juda past.
    """
    day_name = datetime.datetime.now(TIMEZONE).strftime("%A")
    post = generate_daily_greeting(day_name)
    post_content(BOT_TOKEN, CHANNEL_ID, post)
    logger.info(f"Kunlik salomlashish yuborildi: {day_name}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin '✅' yoki '❌' bosganda ishlaydi."""
    query = update.callback_query
    await query.answer()

    action, post_id = query.data.split(":")
    post = pending_posts.pop(post_id, None)

    if post is None:
        try:
            await query.edit_message_caption(caption="⚠️ Bu post allaqachon ko'rib chiqilgan.")
        except Exception:
            await query.edit_message_text("⚠️ Bu post allaqachon ko'rib chiqilgan.")
        return

    if action == "approve":
        post_content(BOT_TOKEN, CHANNEL_ID, post)
        result_text = "✅ Kanalga yuborildi."
    else:
        result_text = "❌ Bekor qilindi."

    try:
        await query.edit_message_caption(caption=result_text)
    except Exception:
        await query.edit_message_text(result_text)


async def cmd_test_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda...")
    await job_grammar(context.application)


async def cmd_test_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda...")
    await job_vocabulary(context.application)


async def cmd_test_idioms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda...")
    await job_idioms(context.application)


async def cmd_test_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda...")
    await job_reading(context.application)


async def cmd_test_greeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Namuna ko'rsatadi, lekin kanalga CHIQMAYDI (faqat admin'ga)."""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    day_name = datetime.datetime.now(TIMEZONE).strftime("%A")
    post = generate_daily_greeting(day_name)
    await update.message.reply_photo(
        photo=_photo_arg(post),
        caption=f"👀 NAMUNA (kanalga chiqmadi):\n\n{_format_to_html(post['text'])}",
        parse_mode="HTML",
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("test_grammar", cmd_test_grammar))
    app.add_handler(CommandHandler("test_vocab", cmd_test_vocab))
    app.add_handler(CommandHandler("test_idioms", cmd_test_idioms))
    app.add_handler(CommandHandler("test_reading", cmd_test_reading))
    app.add_handler(CommandHandler("test_greeting", cmd_test_greeting))
    app.add_handler(CallbackQueryHandler(button_callback))

    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(job_greeting, "cron", hour=7, minute=0, args=[app])
    scheduler.add_job(job_vocabulary, "cron", hour=9, minute=0, args=[app])
    scheduler.add_job(job_grammar, "cron", hour=12, minute=0, args=[app])
    scheduler.add_job(job_idioms, "cron", hour=15, minute=0, args=[app])
    scheduler.add_job(job_reading, "cron", hour=20, minute=0, args=[app])
    scheduler.start()

    logger.info(
        "Bot ishga tushdi. Jadval: 07:00 salomlashish (avtomatik), "
        "09:00 vocabulary+test, 12:00 grammar+test, 15:00 idioms+test, "
        "20:00 reading+test (oxirgi to'rttasi tasdiqlash orqali)"
    )
    app.run_polling()


if __name__ == "__main__":
    main()
