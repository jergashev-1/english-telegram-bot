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


def _markdown_bold_to_html(text: str) -> str:
    """
    Gemini matnda **so'z** (Markdown qalin) formatidan foydalanadi.
    Telegram buni o'zi tushunmaydi (agar parse_mode ko'rsatilmasa),
    shuning uchun buni Telegram HTML formatiga (<b>so'z</b>) o'giramiz —
    natijada so'z HAQIQATAN QALIN (bold) ko'rinishda chiqadi.
    """
    # Avval HTML uchun maxsus belgilarni xavfsiz qilib almashtiramiz
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Agar juft bo'lmagan ** qolib ketgan bo'lsa (masalan AI xatosi),
    # oxirgisini olib tashlaymiz — aks holda HTML noto'g'ri chiqib,
    # Telegram xabarni butunlay rad etadi.
    if text.count("**") % 2 == 1:
        idx = text.rfind("**")
        text = text[:idx] + text[idx + 2:]

    parts = text.split("**")
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(f"<b>{part}</b>")
        else:
            result.append(part)
    return "".join(result)


def _send_long_text(base_url: str, channel_id: str, text: str):
    """
    Telegram xabarlar uchun 4096 belgidan uzun matnni avtomatik ravishda
    bir nechta xabarga bo'lib yuboradi (aks holda Telegram butunlay rad
    etadi yoki kesib tashlaydi).
    """
    response = None
    for i in range(0, len(text), MESSAGE_LIMIT):
        chunk = text[i:i + MESSAGE_LIMIT]
        response = requests.post(
            f"{base_url}/sendMessage",
            data={"chat_id": channel_id, "text": chunk, "parse_mode": "HTML"},
            timeout=30,
        )
        if not response.ok:
            print(f"DEBUG: Telegram javobi: {response.text}")
        response.raise_for_status()
    return response


def post_content(bot_token: str, channel_id: str, post: dict):
    """
    Generatsiya qilingan postni (rasm + matn) to'g'ridan-to'g'ri kanalga
    yuboradi. Matndagi **qalin** belgilar haqiqiy qalin (bold) formatga
    o'giriladi. Agar matn Telegram'ning "caption" chegarasidan (1024
    belgi) uzun bo'lsa, avval rasmni, keyin to'liq matnni alohida
    yuboradi.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"
    html_text = _markdown_bold_to_html(post["text"])

    # Uzunlikni ASL (formatlanmagan) matnga qarab hisoblaymiz —
    # bu Telegram'ning haqiqiy hisoblash usuliga yaqinroq.
    if len(post["text"]) <= CAPTION_LIMIT:
        response = requests.post(
            f"{base_url}/sendPhoto",
            data={
                "chat_id": channel_id,
                "photo": post["image_url"],
                "caption": html_text,
                "parse_mode": "HTML",
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
        response = _send_long_text(base_url, channel_id, html_text)

    if not response.ok:
        print(f"DEBUG: Telegram javobi: {response.text}")
    response.raise_for_status()
    print(f"✅ {post['type']} posti muvaffaqiyatli yuborildi.")
    return response.json()
