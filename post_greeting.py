"""
post_greeting.py
-----------------
GitHub Actions har kuni 07:00 (Toshkent vaqti) da ushbu skriptni ishga
tushiradi. Skript kunga mos salomlashish postini generatsiya qilib,
to'g'ridan-to'g'ri kanalga yuboradi.
"""

import os
import datetime
import zoneinfo

from content_generator import generate_daily_greeting
from telegram_sender import post_content

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
TASHKENT = zoneinfo.ZoneInfo("Asia/Tashkent")

if __name__ == "__main__":
    day_name = datetime.datetime.now(TASHKENT).strftime("%A")
    post = generate_daily_greeting(day_name)
    post_content(TELEGRAM_BOT_TOKEN, CHANNEL_ID, post)
