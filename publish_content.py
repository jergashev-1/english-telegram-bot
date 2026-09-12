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
import base64

from telegram_sender import post_content

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

if __name__ == "__main__":
    with open("content.json", "r", encoding="utf-8") as f:
        post = json.load(f)

    # Agar rasm base64 ko'rinishida saqlangan bo'lsa, uni qaytadan
    # xom baytlarga (bytes) o'giramiz.
    if "image_bytes_b64" in post:
        post["image_bytes"] = base64.b64decode(post.pop("image_bytes_b64"))

    post_content(TELEGRAM_BOT_TOKEN, CHANNEL_ID, post)
