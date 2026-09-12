"""
publish_content.py
-------------------
generate_content.py tomonidan saqlangan content.json faylini o'qib,
Telegram kanaliga yuboradi. Bu skript FAQAT admin GitHub'da
tasdiqlagandan keyin ishga tushadi (workflow'dagi 'environment'
sozlamasi orqali).
"""

import os
import json

from telegram_sender import post_content

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

if __name__ == "__main__":
    with open("content.json", "r", encoding="utf-8") as f:
        post = json.load(f)

    post_content(TELEGRAM_BOT_TOKEN, CHANNEL_ID, post)
