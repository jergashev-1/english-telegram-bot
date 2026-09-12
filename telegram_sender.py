"""
telegram_sender.py
-------------------
GitHub Actions uchun soddalashtirilgan Telegram yuborish moduli.
Endi doimiy ishlaydigan bot (polling) kerak emas — oddiy HTTP so'rov
orqali kanalga post yuboramiz, keyin skript tugaydi.

Bu yerda 'requests' kutubxonasidan foydalaniladi (juda sodda va yengil).
"""

import requests

CAPTION_LIMIT = 1024
MESSAGE_LIMIT = 4096


def _send_long_text(base_url: str, channel_id: str, text: str):
    """
    Telegram xabarlar uchun 4096 belgidan uzun matnni avtomatik ravishda
    bir nechta xabarga bo'lib yuboradi (aks holda Telegram butunlay rad
    etadi yoki kesib tashlaydi).
    """
    for i in range(0, len(text), MESSAGE_LIMIT):
        chunk = text[i:i + MESSAGE_LIMIT]
        response = requests.post(
            f"{base_url}/sendMessage",
            data={"chat_id": channel_id, "text": chunk},
            timeout=30,
        )
        if not response.ok:
            print(f"DEBUG: Telegram javobi: {response.text}")
        response.raise_for_status()
    return response


def post_content(bot_token: str, channel_id: str, post: dict):
    """
    Generatsiya qilingan postni (rasm + matn) to'g'ridan-to'g'ri kanalga
    yuboradi. Agar matn Telegram'ning "caption" chegarasidan (1024 belgi)
    uzun bo'lsa, avval rasmni, keyin to'liq matnni alohida yuboradi.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"

    # Diagnostika uchun: CHANNEL_ID qanday qiymat ekanini (uzunligi bilan)
    # log'ga chiqaramiz — bo'shliq yoki ko'rinmas belgilarni aniqlash uchun.
    print(f"DEBUG: CHANNEL_ID qiymati={channel_id!r} (uzunligi: {len(channel_id)})")

    if len(post["text"]) <= CAPTION_LIMIT:
        response = requests.post(
            f"{base_url}/sendPhoto",
            data={
                "chat_id": channel_id,
                "photo": post["image_url"],
                "caption": post["text"],
            },
            timeout=30,
        )
    else:
        # Avval rasmni yuboramiz
        response = requests.post(
            f"{base_url}/sendPhoto",
            data={"chat_id": channel_id, "photo": post["image_url"]},
            timeout=30,
        )
        if not response.ok:
            print(f"DEBUG: Telegram javobi: {response.text}")
        response.raise_for_status()
        # Keyin to'liq matnni (kerak bo'lsa bir nechta xabarga bo'lib) yuboramiz
        response = _send_long_text(base_url, channel_id, post["text"])

    if not response.ok:
        print(f"DEBUG: Telegram javobi: {response.text}")
    response.raise_for_status()
    print(f"✅ {post['type']} posti muvaffaqiyatli yuborildi.")
    return response.json()
