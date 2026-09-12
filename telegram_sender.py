"""
telegram_sender.py
-------------------
GitHub Actions uchun soddalashtirilgan Telegram yuborish moduli.
Endi doimiy ishlaydigan bot (polling) kerak emas — oddiy HTTP so'rov
orqali kanalga post yuboramiz, keyin skript tugaydi.

Bu modul ikkala holatni ham qo'llab-quvvatlaydi:
- post["image_bytes"] — Gemini orqali generatsiya qilingan rasm (asosiy holat)
- post["image_url"] — Pollinations orqali (fallback holat)
"""

import requests

CAPTION_LIMIT = 1024
MESSAGE_LIMIT = 4096


def _pairs_to_tag(text: str, delimiter: str, tag: str) -> str:
    """
    Matndagi juft belgilar orasidagi qismni berilgan HTML teg bilan
    o'raydi (masalan **so'z** -> <b>so'z</b>, yoki ||javob|| -> spoiler).
    """
    if text.count(delimiter) % 2 == 1:
        idx = text.rfind(delimiter)
        text = text[:idx] + text[idx + len(delimiter):]

    parts = text.split(delimiter)
    result = []
    for i, part in enumerate(parts):
        result.append(f"<{tag}>{part}</{tag}>" if i % 2 == 1 else part)
    return "".join(result)


def _format_to_html(text: str) -> str:
    """
    Gemini matnida ishlatiladigan ikki formatlashni Telegram HTML'ga
    o'giradi:
    - **so'z**       -> <b>so'z</b>           (qalin harf)
    - ||javob matni|| -> <tg-spoiler>...</tg-spoiler>  (bosib ochiladigan,
      "spoiler" ko'rinish — testning javoblarini yashirish uchun)
    """
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _pairs_to_tag(text, "**", "b")
    text = _pairs_to_tag(text, "||", "tg-spoiler")
    return text


def _send_long_text(base_url: str, channel_id: str, text: str):
    """4096 belgidan uzun matnni bir nechta xabarga bo'lib yuboradi."""
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


def _send_photo(base_url: str, channel_id: str, post: dict, caption: str = None):
    """
    Rasmni yuboradi — post['image_bytes'] mavjud bo'lsa, uni to'g'ridan-
    to'g'ri fayl sifatida (multipart) yuboradi; aks holda post['image_url']
    orqali (havola sifatida) yuboradi.
    """
    data = {"chat_id": channel_id}
    if caption is not None:
        data["caption"] = caption
        data["parse_mode"] = "HTML"

    if "image_bytes" in post:
        files = {"photo": ("image.png", post["image_bytes"], "image/png")}
        response = requests.post(f"{base_url}/sendPhoto", data=data, files=files, timeout=60)
    else:
        data["photo"] = post["image_url"]
        response = requests.post(f"{base_url}/sendPhoto", data=data, timeout=30)

    return response


def post_content(bot_token: str, channel_id: str, post: dict):
    """
    Generatsiya qilingan postni (rasm + matn) to'g'ridan-to'g'ri kanalga
    yuboradi. Matndagi **qalin** belgilar haqiqiy qalin (bold) formatga
    o'giriladi. Agar matn 1024 belgidan uzun bo'lsa, avval rasmni, keyin
    to'liq matnni alohida yuboradi.
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"
    html_text = _format_to_html(post["text"])

    if len(post["text"]) <= CAPTION_LIMIT:
        response = _send_photo(base_url, channel_id, post, caption=html_text)
    else:
        response = _send_photo(base_url, channel_id, post)
        if not response.ok:
            print(f"DEBUG: Telegram javobi: {response.text}")
        response.raise_for_status()
        response = _send_long_text(base_url, channel_id, html_text)

    if not response.ok:
        print(f"DEBUG: Telegram javobi: {response.text}")
    response.raise_for_status()
    print(f"✅ {post['type']} posti muvaffaqiyatli yuborildi.")
    return response.json()
