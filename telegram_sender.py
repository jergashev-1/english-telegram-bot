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
        # Keyin to'liq matnni alohida xabar sifatida yuboramiz
        response = requests.post(
            f"{base_url}/sendMessage",
            data={"chat_id": channel_id, "text": post["text"]},
            timeout=30,
        )

    if not response.ok:
        print(f"DEBUG: Telegram javobi: {response.text}")
    response.raise_for_status()
    print(f"✅ {post['type']} posti muvaffaqiyatli yuborildi.")
    return response.json()
