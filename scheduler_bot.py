"""
scheduler_bot.py
-----------------
Bu skript mavjud Telegram botingizga QO'SHIMCHA funksiya sifatida ishlaydi:
- Kunning turli vaqtlarida grammar / vocabulary / idioms / reading test
  MATNI VA MOS RASMINI generatsiya qiladi
- Avval SIZGA (admin) shaxsiy chatga yuboradi, tasdiqlash uchun (rasm + matn)
- Siz "✅ Tasdiqlash" tugmasini bossangiz — kanalga (rasm + matn) chiqadi
- "❌ Rad etish" bossangiz — o'sha post chiqmaydi

O'RNATISH:
    pip install python-telegram-bot google-generativeai apscheduler

ISHGA TUSHIRISH:
    export TELEGRAM_BOT_TOKEN="sizning_botfather_tokeningiz"
    export GEMINI_API_KEY="sizning_bepul_gemini_kalitingiz"
    export ADMIN_CHAT_ID="sizning_shaxsiy_telegram_id"
    export CHANNEL_ID="@sizning_kanal_username_yoki_id"
    python scheduler_bot.py
"""

import os
import logging
import datetime
import zoneinfo
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
CHANNEL_ID = os.environ["CHANNEL_ID"]
TIMEZONE = zoneinfo.ZoneInfo("Asia/Tashkent")

# Tasdiqlanishi kutilayotgan postlarni vaqtincha saqlash uchun
# Har bir post endi {"text": ..., "image_url": ...} ko'rinishida saqlanadi
pending_posts: dict[str, dict] = {}
_post_counter = 0

# Telegram caption (rasm ostidagi matn) uzunlik chegarasi
CAPTION_LIMIT = 1024


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

    # Rasm va matnni ko'rib chiqish uchun yuboramiz
    if len(post["text"]) <= CAPTION_LIMIT:
        await app.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=post["image_url"],
            caption=post["text"],
            reply_markup=keyboard,
        )
    else:
        # Matn caption chegarasidan uzun bo'lsa, rasm va matnni alohida yuboramiz
        await app.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=post["image_url"])
        await app.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=post["text"],
            reply_markup=keyboard,
        )


async def job_grammar(app: Application):
    post = generate_grammar_post()
    await _send_for_approval(app, post)


async def job_vocabulary(app: Application):
    post = generate_vocabulary_post()
    await _send_for_approval(app, post)


async def job_idioms(app: Application):
    post = generate_idiom_post()
    await _send_for_approval(app, post)


async def job_reading(app: Application):
    post = generate_reading_test()
    await _send_for_approval(app, post)


async def job_greeting(app: Application):
    """
    Har kuni ertalab 07:00'da ishlaydi. Boshqa postlardan farqli o'laroq,
    BU TO'G'RIDAN-TO'G'RI kanalga chiqadi (tasdiqlashsiz) — chunki oddiy
    salomlashish xabari xato bo'lish xavfi juda past. Agar buni ham
    tasdiqlash orqali chiqishini xohlasangiz, pastdagi eslatmaga qarang.
    """
    day_name = datetime.datetime.now(TIMEZONE).strftime("%A")
    post = generate_daily_greeting(day_name)
    await app.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=post["image_url"],
        caption=post["text"],
    )
    logger.info(f"Kunlik salomlashish yuborildi: {day_name}")

    # AGAR TASDIQLASH ORQALI CHIQISHINI XOHLASANGIZ — yuqoridagi 3 qatorni
    # o'chirib, o'rniga quyidagini yozing:
    #     await _send_for_approval(app, post)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin '✅' yoki '❌' bosganda ishlaydi."""
    query = update.callback_query
    await query.answer()

    action, post_id = query.data.split(":")
    post = pending_posts.pop(post_id, None)

    if post is None:
        await query.edit_message_caption(caption="⚠️ Bu post allaqachon ko'rib chiqilgan.")
        return

    if action == "approve":
        if len(post["text"]) <= CAPTION_LIMIT:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=post["image_url"],
                caption=post["text"],
            )
        else:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=post["image_url"])
            await context.bot.send_message(chat_id=CHANNEL_ID, text=post["text"])

        try:
            await query.edit_message_caption(caption="✅ Kanalga yuborildi.")
        except Exception:
            await query.edit_message_text("✅ Kanalga yuborildi.")
    else:
        try:
            await query.edit_message_caption(caption="❌ Bekor qilindi.")
        except Exception:
            await query.edit_message_text("❌ Bekor qilindi.")


async def cmd_test_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qo'lda tekshirish uchun: /test_grammar buyrug'i darhol post generatsiya qiladi."""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda (matn + rasm)...")
    await job_grammar(context.application)


async def cmd_test_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda (matn + rasm)...")
    await job_vocabulary(context.application)


async def cmd_test_idioms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda (matn + rasm)...")
    await job_idioms(context.application)


async def cmd_test_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("Generatsiya qilinmoqda (matn + rasm)...")
    await job_reading(context.application)


async def cmd_test_greeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Salomlashish namunasini ko'rish uchun — bu FAQAT SIZGA (admin) yuboradi,
    kanalga CHIQMAYDI. Haqiqiy avtomatik salomlashishni ko'rish uchun
    ertalab 07:00'ni kuting yoki kanalni tekshiring.
    """
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    day_name = datetime.datetime.now(TIMEZONE).strftime("%A")
    post = generate_daily_greeting(day_name)
    await update.message.reply_photo(
        photo=post["image_url"],
        caption=f"👀 NAMUNA (kanalga chiqmadi):\n\n{post['text']}",
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Qo'lda test qilish buyruqlari (mavjud botingizga qo'shimcha sifatida)
    app.add_handler(CommandHandler("test_grammar", cmd_test_grammar))
    app.add_handler(CommandHandler("test_vocab", cmd_test_vocab))
    app.add_handler(CommandHandler("test_idioms", cmd_test_idioms))
    app.add_handler(CommandHandler("test_reading", cmd_test_reading))
    app.add_handler(CommandHandler("test_greeting", cmd_test_greeting))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Avtomatik jadval: siz belgilagan qat'iy vaqtlar
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
