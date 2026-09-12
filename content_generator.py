"""
content_generator.py
---------------------
Bu modul Google Gemini API (BEPUL reja) yordamida kunlik ingliz tili
kontentini (grammar, vocabulary, idioms, reading test) va har biriga mos
ILLUSTRATSIYA (rasm) ni avtomatik generatsiya qiladi.

MATN UCHUN — Google Gemini API (BEPUL):
    pip install google-generativeai
    Bepul kalit: https://aistudio.google.com/apikey (kredit karta shart emas)

RASM UCHUN — Pollinations.ai (BUTUNLAY BEPUL, kalit shart emas):
    Hech qanday ro'yxatdan o'tish, hech qanday API kalit kerak emas.
    Oddiy HTTP so'rov orqali ishlaydi — shuning uchun kod ancha sodda.
    Rasmiy sayt: https://pollinations.ai

Har bir funksiya endi dict qaytaradi:
    {
        "type": "GRAMMAR" / "VOCABULARY" / "IDIOMS" / "READING",
        "text": "...",          # Telegram posti matni
        "image_url": "...",     # to'g'ridan-to'g'ri Telegram'ga yuborsa bo'ladigan rasm havolasi
    }
"""

import os
import random
import urllib.parse
import google.generativeai as genai

# API kalitni environment variable orqali olamiz (xavfsizlik uchun)
# Terminal'da o'rnatish: export GEMINI_API_KEY="AIzaSy..."
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "gemini-3.6-flash"

# Har kuni turli mavzular chiqishi uchun oddiy ro'yxat
GRAMMAR_TOPICS = [
    "Present Simple vs Present Continuous",
    "Past Simple", "Present Perfect", "Future Forms (will vs going to)",
    "Conditionals (0 and 1st)", "Modal verbs (can, must, should)",
    "Passive Voice (basic)", "Comparatives and Superlatives",
    "Articles (a/an/the)", "Prepositions of time and place",
]

VOCAB_THEMES = [
    "Travel and Transportation", "Food and Cooking", "Work and Office Life",
    "Health and Body", "Technology and Internet", "Emotions and Feelings",
    "Shopping and Money", "Weather and Seasons", "Family and Relationships",
    "Hobbies and Free Time",
]

IDIOM_THEMES = [
    "idioms about time", "idioms about money", "idioms about emotions",
    "idioms about success and failure", "idioms about relationships",
    "animal idioms", "food idioms", "weather idioms",
]

# Har bir hafta kuni uchun boshqacha kayfiyat/mavzu — rasm va matnga xilma-xillik beradi
DAY_THEMES = {
    "Monday": "fresh start energy, sunrise, a cup of coffee, new week motivation",
    "Tuesday": "steady progress, a small growing plant, quiet focus",
    "Wednesday": "midweek balance, a half-finished path in a forest, calm",
    "Thursday": "building momentum, warm afternoon sunlight, almost there feeling",
    "Friday": "excitement, bright colors, weekend anticipation",
    "Saturday": "relaxation, a cozy reading corner, leisure morning",
    "Sunday": "peaceful rest, a calm sunrise, preparing for a new week",
}


def _ask_gemini(prompt: str, max_tokens: int = 800) -> str:
    """Gemini API'ga so'rov yuboradi va matn javobini qaytaradi."""
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
    )
    return response.text.strip()


def _build_image_url(description: str) -> str:
    """
    Pollinations.ai orqali BEPUL rasm havolasini quradi.
    Bu havola to'g'ridan-to'g'ri Telegram'ning send_photo funksiyasiga
    berilishi mumkin — rasmni oldindan yuklab olish shart emas.

    model=flux — Pollinations'ning yuqori sifatli rasm modeli (standart
    "turbo" modelidan ancha aniq va sifatli natija beradi).
    """
    style = (
        "professional digital illustration, highly detailed, vibrant "
        "colors, sharp focus, high quality, clean composition, "
        "no text, no words, no letters, no signature"
    )
    full_prompt = f"{description}, {style}"
    encoded = urllib.parse.quote(full_prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1200&height=800&nologo=true&model=flux&enhance=true&seed={random.randint(1, 999999)}"
    )


def generate_grammar_post() -> dict:
    """Kunlik grammar posti + 4 ta test savoli + mos illustratsiya generatsiya qiladi."""
    topic = random.choice(GRAMMAR_TOPICS)
    prompt = f"""
Siz ingliz tili o'qituvchisisiz. Telegram kanali uchun "{topic}" mavzusida
post yozing. Post AYNAN quyidagi tuzilishga ega bo'lsin:

📚 GRAMMAR: {topic}

- Qoidaning 1-2 gapli sodda tushuntirilishi (ingliz tilida)
- 3 ta misol gap
- 1 ta tez-tez uchraydigan xato va uni tuzatish

🧪 TEST — Quyidagi 4 ta savol albatta shu YUQORIDAGI qoida asosida
tuzilgan bo'lsin (boshqa mavzudan emas):

1. [savol matni]
   A) ... B) ... C) ...
2. [savol matni]
   A) ... B) ... C) ...
3. [savol matni]
   A) ... B) ... C) ...
4. [savol matni]
   A) ... B) ... C) ...

Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]

Postni Telegram formatida yozing (emoji ishlatilsin, lekin oshirib
yubormang). Faqat post matnini yozing, boshqa izoh bermang.
"""
    text = _ask_gemini(prompt, max_tokens=2200)
    image_url = _build_image_url(
        f"A clear educational illustration explaining the English grammar "
        f"topic '{topic}', showing a classroom whiteboard or diagram with "
        f"arrows connecting example sentences, teacher-style visual"
    )
    return {"type": "GRAMMAR", "text": text, "image_url": image_url}


def generate_vocabulary_post() -> dict:
    """Kunlik lug'at (vocabulary) posti + 4 ta test savoli + mos illustratsiya generatsiya qiladi."""
    theme = random.choice(VOCAB_THEMES)
    prompt = f"""
Siz ingliz tili o'qituvchisisiz. Telegram kanali uchun "{theme}" mavzusida
post yozing. Post AYNAN quyidagi tuzilishga ega bo'lsin:

📖 VOCABULARY: {theme}

5 ta foydali so'z/ibora, har biri uchun:
- So'z (talaffuz bilan, agar murakkab bo'lsa)
- Qisqa ta'rif (inglizcha)
- 1 ta misol gap

🧪 TEST — Quyidagi 4 ta savol albatta shu YUQORIDAGI so'zlar asosida
tuzilgan bo'lsin (masalan, "so'zni ta'rifiga moslashtiring" yoki
"gapga mos so'zni tanlang" formatida):

1. [savol matni]
   A) ... B) ... C) ...
2. [savol matni]
   A) ... B) ... C) ...
3. [savol matni]
   A) ... B) ... C) ...
4. [savol matni]
   A) ... B) ... C) ...

Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]

Postni Telegram formatida yozing (emoji o'rinli ishlatilsin).
Faqat post matnini yozing, boshqa izoh bermang.
"""
    text = _ask_gemini(prompt, max_tokens=2200)
    image_url = _build_image_url(
        f"A vivid, realistic scene clearly depicting the everyday theme of "
        f"'{theme}', with recognizable objects and people related to this "
        f"topic, warm lighting, magazine-quality photo-illustration"
    )
    return {"type": "VOCABULARY", "text": text, "image_url": image_url}


def generate_idiom_post() -> dict:
    """Kunlik idioma posti + 4 ta test savoli + mos illustratsiya generatsiya qiladi."""
    theme = random.choice(IDIOM_THEMES)
    prompt = f"""
Siz ingliz tili o'qituvchisisiz. Telegram kanali uchun "{theme}" mavzusida
post yozing. Post AYNAN quyidagi tuzilishga ega bo'lsin:

💡 IDIOMS: {theme}

3 ta ingliz idiomasi, har biri uchun:
- Idioma (qalin harflarda)
- Ma'nosi (oddiy inglizcha tushuntirish)
- 1 ta misol gap

🧪 TEST — Quyidagi 4 ta savol albatta shu YUQORIDAGI idiomalar asosida
tuzilgan bo'lsin (masalan, "bu idioma nimani anglatadi" yoki "gapga mos
idiomani tanlang" formatida):

1. [savol matni]
   A) ... B) ... C) ...
2. [savol matni]
   A) ... B) ... C) ...
3. [savol matni]
   A) ... B) ... C) ...
4. [savol matni]
   A) ... B) ... C) ...

Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]

Postni Telegram formatida yozing (emoji o'rinli ishlatilsin).
Faqat post matnini yozing, boshqa izoh bermang.
"""
    text = _ask_gemini(prompt, max_tokens=2200)
    image_url = _build_image_url(
        f"A creative, literal visual metaphor artwork illustrating the "
        f"theme of '{theme}' in a fun, storybook illustration style, "
        f"whimsical and imaginative scene"
    )
    return {"type": "IDIOMS", "text": text, "image_url": image_url}


def generate_reading_test() -> dict:
    """Reading matni + 4 ta tushunish savoli + mos illustratsiya generatsiya qiladi."""
    prompt = """
Siz ingliz tili o'qituvchisisiz. Telegram kanali uchun qisqa (100-150 so'zli)
reading matni yozing (intermediate daraja), so'ngra AYNAN o'sha matn
asosida 4 ta tushunish savoli (multiple choice, A/B/C variantlari bilan)
qo'shing. Tuzilma:

📝 READING TEST

[Matn]

🧪 Savollar:
1. [savol matni]
   A) ... B) ... C) ...
2. [savol matni]
   A) ... B) ... C) ...
3. [savol matni]
   A) ... B) ... C) ...
4. [savol matni]
   A) ... B) ... C) ...

Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]

Faqat post matnini yozing, boshqa izoh bermang.
"""
    text = _ask_gemini(prompt, max_tokens=2200)
    image_url = _build_image_url(
        "A cozy, realistic photo-illustration of a person reading an open "
        "book in a quiet library or study corner, warm ambient lighting, "
        "detailed and inviting"
    )
    return {"type": "READING", "text": text, "image_url": image_url}


def generate_daily_greeting(day_name: str) -> dict:
    """
    Kunga mos, xilma-xil salomlashish posti generatsiya qiladi
    (masalan: "Have a nice Monday!"). Har safar boshqacha ifoda bilan
    yoziladi — bir xil takrorlanmaslik uchun Gemini'dan foydalaniladi.
    """
    theme = DAY_THEMES.get(day_name, "a fresh, cheerful morning")
    prompt = f"""
You are a friendly English teacher writing a short good-morning message
for a Telegram channel of English learners and teachers. Today is
{day_name}.

Write a warm, upbeat 1-2 sentence morning greeting in English wishing
everyone a nice {day_name}. Use natural, varied phrasing — do not always
start the same way. Include 1-2 relevant emojis. Keep it under 200
characters. Output ONLY the greeting message, nothing else.
"""
    text = _ask_gemini(prompt)
    image_url = _build_image_url(
        f"A beautiful, realistic photo-illustration capturing the mood of "
        f"{theme}, warm and inviting morning atmosphere, high quality"
    )
    return {"type": "GREETING", "text": text, "image_url": image_url}


# Test qilish uchun (to'g'ridan-to'g'ri ishga tushirilsa)
if __name__ == "__main__":
    for generator in (
        generate_grammar_post,
        generate_vocabulary_post,
        generate_idiom_post,
        generate_reading_test,
    ):
        result = generator()
        print(f"=== {result['type']} ===")
        print(result["text"])
        print("IMAGE:", result["image_url"])
        print()

    greeting = generate_daily_greeting("Monday")
    print("=== GREETING (Monday) ===")
    print(greeting["text"])
    print("IMAGE:", greeting["image_url"])
