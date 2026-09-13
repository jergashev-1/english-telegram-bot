"""
content_generator.py
---------------------
Bu modul Google Gemini API (BEPUL reja) yordamida kunlik ingliz tili
kontentini (grammar, vocabulary, idioms, reading test) va har biriga mos
ILLUSTRATSIYA (rasm) ni avtomatik generatsiya qiladi.

MATN VA RASM UCHUN — Google Gemini API (BEPUL, bir xil kalit):
    pip install google-generativeai
    Bepul kalit: https://aistudio.google.com/apikey (kredit karta shart emas)
    Matn uchun: gemini-3.6-flash
    Rasm uchun: gemini-2.5-flash-image ("Nano Banana")

ZAXIRA RASM MANBAI — Pollinations.ai (agar Gemini rasm modeli
ishlamay qolsa, avtomatik shunga o'tiladi):
    Rasmiy sayt: https://pollinations.ai

ANIQ RASM UCHUN YONDASHUV:
    Gemini'ning o'ziga har bir post oxirida "bu post uchun rasmda aynan
    nima chizish kerak" degan qisqa tavsifni alohida, maxsus qatorda
    ("IMAGE_SCENE: ...") yozishni so'raymiz. Keyin shu qatorni matndan
    ajratib olib (foydalanuvchiga ko'rinmaydi), aynan shu tavsif asosida
    rasm chizdiramiz. Bu umumiy/mavhum mavzu nomidan ko'ra ancha aniq
    va mos rasm beradi.

Har bir funksiya endi dict qaytaradi:
    {
        "type": "GRAMMAR" / "VOCABULARY" / "IDIOMS" / "READING",
        "text": "...",          # Telegram posti matni (IMAGE_SCENE qatorisiz)
        "image_bytes": b"...",  # Gemini orqali generatsiya qilingan rasm (asosiy holat)
        # YOKI
        "image_url": "...",     # Pollinations orqali (faqat fallback holatida)
    }
"""

import os
import re
import base64
import random
import urllib.parse
import google.generativeai as genai

# API kalitni environment variable orqali olamiz (xavfsizlik uchun)
# Terminal'da o'rnatish: export GEMINI_API_KEY="AIzaSy..."
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "gemini-3.6-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

# Har kuni turli mavzular chiqishi uchun oddiy ro'yxat
GRAMMAR_TOPICS = [
    "Present Simple vs Present Continuous",
    "Past Simple", "Present Perfect", "Present Perfect Continuous",
    "Past Continuous", "Past Perfect", "Future Forms (will vs going to)",
    "Future Continuous", "Conditionals (0 and 1st)",
    "Conditionals (2nd and 3rd)", "Mixed Conditionals",
    "Modal verbs (can, must, should)", "Modal verbs of deduction (must/might/can't)",
    "Passive Voice (basic)", "Passive Voice (advanced)",
    "Comparatives and Superlatives", "Articles (a/an/the)",
    "Prepositions of time and place", "Reported Speech (statements)",
    "Reported Speech (questions)", "Relative Clauses (who/which/that)",
    "Gerunds vs Infinitives", "Used to vs Would", "Question Tags",
    "Countable and Uncountable Nouns", "Quantifiers (much/many/a lot of)",
    "Phrasal Verbs with Get", "Phrasal Verbs with Take",
    "So vs Such", "Too vs Enough",
]

VOCAB_THEMES = [
    "Travel and Transportation", "Food and Cooking", "Work and Office Life",
    "Health and Body", "Technology and Internet", "Emotions and Feelings",
    "Shopping and Money", "Weather and Seasons", "Family and Relationships",
    "Hobbies and Free Time", "Education and School", "Sports and Exercise",
    "Environment and Nature", "Housing and Living Spaces", "Clothes and Fashion",
    "Crime and Law", "Media and News", "Art and Culture",
    "Science and Discovery", "Music and Entertainment", "Business and Careers",
    "Social Media and Communication", "Personality Traits", "City Life",
    "Countryside and Farming", "Holidays and Celebrations",
    "Cars and Driving", "Medicine and Illness",
]

IDIOM_THEMES = [
    "idioms about time", "idioms about money", "idioms about emotions",
    "idioms about success and failure", "idioms about relationships",
    "animal idioms", "food idioms", "weather idioms",
    "idioms about work", "idioms about health", "idioms about communication",
    "idioms about problems and difficulties", "idioms about opportunities",
    "idioms about secrets", "idioms about effort and hard work",
    "idioms about surprise", "idioms about anger", "idioms about happiness",
    "body part idioms", "color idioms", "idioms about decisions",
    "sports idioms used in everyday English", "idioms about luck",
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

# Har bir prompt oxiriga qo'shiladigan umumiy ko'rsatma — Gemini'dan
# rasm uchun aniq sahna tavsifini alohida qatorda so'raymiz.
_IMAGE_SCENE_INSTRUCTION = """

Postning ENG OXIRIGA, alohida qatorda, AYNAN quyidagi formatda yozing
(bu qator foydalanuvchiga ko'rinmaydi, faqat rasm chizish uchun ishlatiladi):

IMAGE_SCENE: [shu postning asosiy g'oyasini yoki eng birinchi misolini
LITERAL (so'zma-so'z) tasvirlaydigan, ingliz tilida, 15-25 so'zli aniq
sahna tavsifi — masalan grammar uchun aynan o'sha misol jumlada
tasvirlangan voqeani chizing, idioma uchun idiomaning so'zma-so'z
ma'nosini (masalan "under the weather" — kasal, xafa kayfiyatli odam)
chizing, vocabulary uchun o'sha so'zning aniq ma'nosini ko'rsatadigan
sahnani chizing]
"""


def _ask_gemini(prompt: str, max_tokens: int = 800) -> str:
    """Gemini API'ga so'rov yuboradi va matn javobini qaytaradi."""
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
    )
    return response.text.strip()


def _extract_scene(text: str) -> tuple[str, str | None]:
    """
    Matn oxiridagi 'IMAGE_SCENE: ...' qatorini ajratib oladi va uni asosiy
    matndan olib tashlaydi (foydalanuvchi buni ko'rmasligi kerak).
    Qaytaradi: (tozalangan_matn, sahna_tavsifi_yoki_None)
    """
    match = re.search(r"IMAGE_SCENE:\s*(.+)", text, re.IGNORECASE)
    if not match:
        return text.strip(), None
    scene = match.group(1).strip()
    clean_text = text[:match.start()].strip()
    return clean_text, scene


def _build_image_url(description: str) -> str:
    """
    ZAXIRA (fallback) variant: Pollinations.ai orqali BEPUL rasm havolasini
    quradi. Bu FAQAT agar Gemini'ning o'z rasm modeli ishlamay qolsa
    ishlatiladi (masalan kvota tugasa yoki model nomi o'zgargan bo'lsa).
    """
    style = (
        "professional digital illustration, highly detailed, vibrant "
        "colors, sharp focus, high quality, clean composition, "
        "no text, no words, no letters, no signature, no chalkboard writing"
    )
    full_prompt = f"{description}, {style}"
    encoded = urllib.parse.quote(full_prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1200&height=800&nologo=true&model=flux&enhance=true&seed={random.randint(1, 999999)}"
    )


_cached_image_model_name = None


def _discover_image_model() -> str | None:
    """
    Hisobingizda haqiqatda mavjud bo'lgan rasm generatsiya modelini
    AVTOMATIK ravishda topadi (qattiq yozilgan nom o'rniga). Bu model
    nomlari o'zgarib turgan taqdirda ham tizim ishlashda davom etishini
    ta'minlaydi — sizga loglarni tekshirish shart bo'lmaydi.
    """
    global _cached_image_model_name
    if _cached_image_model_name is not None:
        return _cached_image_model_name

    try:
        candidates = []
        for m in genai.list_models():
            name = m.name.replace("models/", "")
            methods = getattr(m, "supported_generation_methods", [])
            if "generateContent" in methods and "image" in name.lower():
                candidates.append(name)

        # Afzallik tartibi: "flash-image" nomli modellar odatda bepul
        # rejaga ega bo'ladi, "pro-image" esa ko'pincha pullik.
        candidates.sort(key=lambda n: (0 if "flash" in n.lower() else 1, n))

        if candidates:
            _cached_image_model_name = candidates[0]
            print(f"🔍 Topilgan rasm modeli: {_cached_image_model_name}")
            return _cached_image_model_name
    except Exception as e:
        print(f"⚠️ Modellar ro'yxatini olishda xato: {e}")

    return None


def _generate_image(description: str) -> dict:
    """
    Avval hisobingizda mavjud bo'lgan Gemini rasm modelini (Nano Banana)
    AVTOMATIK topib, shu orqali rasm chizishga harakat qiladi — bu
    odatda Pollinations'dan ancha aniq va sifatli natija beradi, va bir
    xil (bepul) API kalitingiz bilan ishlaydi.

    Agar biror sababga ko'ra (masalan kvota tugagan, mos model
    topilmagan) bu ishlamasa, avtomatik ravishda Pollinations.ai'ga
    (URL asosida) qaytadi — shunda tizim baribir ishlashda davom etadi.

    Natija: {"image_bytes": bytes} (Gemini muvaffaqiyatli bo'lsa)
            yoki {"image_url": str} (fallback holatida)
    """
    style = (
        "professional digital illustration, highly detailed, vibrant "
        "colors, sharp focus, high quality, clean composition, "
        "no text, no words, no letters, no signature"
    )
    full_prompt = f"{description}, {style}"

    model_name = _discover_image_model() or IMAGE_MODEL

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)
        for part in response.candidates[0].content.parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data is not None and inline_data.data:
                raw_data = inline_data.data
                # Ba'zida SDK ma'lumotni base64 matn sifatida qaytarishi
                # mumkin — bu holatni ham xavfsiz qayta ishlaymiz.
                if isinstance(raw_data, str):
                    raw_data = base64.b64decode(raw_data)
                print(f"✅ Rasm '{model_name}' modeli orqali generatsiya qilindi.")
                return {"image_bytes": raw_data}
        raise RuntimeError("Gemini javobida rasm topilmadi")
    except Exception as e:
        print(f"⚠️ Gemini rasm generatsiyasi ishlamadi ({e}), Pollinations'ga o'tilmoqda...")
        return {"image_url": _build_image_url(description)}


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

||Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]||

Postni Telegram formatida yozing (emoji ishlatilsin, lekin oshirib
yubormang). Faqat post matnini yozing, boshqa izoh bermang.
{_IMAGE_SCENE_INSTRUCTION}
"""
    raw = _ask_gemini(prompt, max_tokens=2200)
    text, scene = _extract_scene(raw)
    image_result = _generate_image(scene or f"a scene literally illustrating '{topic}'")
    return {"type": "GRAMMAR", "text": text, **image_result}


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

||Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]||

Postni Telegram formatida yozing (emoji o'rinli ishlatilsin).
Faqat post matnini yozing, boshqa izoh bermang.
{_IMAGE_SCENE_INSTRUCTION}
"""
    raw = _ask_gemini(prompt, max_tokens=2200)
    text, scene = _extract_scene(raw)
    image_result = _generate_image(scene or f"a scene about the theme '{theme}'")
    return {"type": "VOCABULARY", "text": text, **image_result}


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

||Javoblar: 1-[harf], 2-[harf], 3-[harf], 4-[harf]||

Postni Telegram formatida yozing (emoji o'rinli ishlatilsin).
Faqat post matnini yozing, boshqa izoh bermang.
{_IMAGE_SCENE_INSTRUCTION}
"""
    raw = _ask_gemini(prompt, max_tokens=2200)
    text, scene = _extract_scene(raw)
    image_result = _generate_image(scene or f"a literal depiction of {theme}")
    return {"type": "IDIOMS", "text": text, **image_result}


READING_TOPICS = [
    "free time and hobbies", "university student life", "working from home",
    "healthy eating habits", "travel experiences", "learning a new language",
    "social media and technology", "environmental protection",
    "sports and fitness", "friendship and relationships",
    "family traditions", "moving to a new city", "starting a new job",
    "cooking and favorite foods", "reading books", "music and concerts",
    "pets and animals", "weekend routines", "childhood memories",
    "online shopping", "public transportation", "seasons and weather",
    "part-time jobs for students", "volunteering", "photography as a hobby",
    "dealing with stress", "sleep habits", "morning routines",
    "learning to drive", "living with roommates", "planning a vacation",
    "using smartphones too much", "trying a new hobby",
    "differences between city and village life",
]


def generate_reading_test() -> dict:
    """
    Reading uchun 'gap-fill' (bo'sh joylarni to'ldirish) mashqi
    generatsiya qiladi (rasmsiz). Har bir bo'sh joy uchun javob —
    matnning BOSHQA qismida allaqachon ishlatilgan so'z bo'lishi kerak
    (ya'ni javoblarni matnning o'zidan topish mumkin).
    """
    topic = random.choice(READING_TOPICS)
    prompt = f"""
Siz ingliz tili o'qituvchisisiz. Telegram kanali uchun "{topic}" mavzusida,
birinchi shaxs tilida (I, my) yozilgan, tabiiy va qiziqarli qisqa matn
(120-160 so'z, intermediate daraja) yozing.

MUHIM QOIDA: Matnda 6 ta bo'sh joy (gap) bo'lishi kerak, quyidagi
formatda: (1)__________, (2)__________ va h.k. Har bir bo'sh joy uchun
to'g'ri javob — bitta so'z bo'lishi SHART, va bu so'z MATNNING BOSHQA
BIR JOYIDA ALLAQACHON ishlatilgan bo'lishi kerak (ya'ni o'quvchi javobni
matnning o'zidan topib, ko'chirib yozishi mumkin). Masalan, agar matnda
biror joyda "gym" so'zi ishlatilgan bo'lsa, boshqa bir bo'sh joy javobi
ham "gym" bo'lishi mumkin.

Tuzilma AYNAN quyidagicha bo'lsin:

📝 READING TEST

Read the text. Fill in each gap with ONE word. You must use a word
which is somewhere else in the text.

[Sarlavha savol shaklida, masalan "What do you do in your free time?"]

[120-160 so'zli matn, ichida (1)__________ dan (6)__________ gacha
6 ta bo'sh joy bilan]

||Javoblar: 1-[so'z], 2-[so'z], 3-[so'z], 4-[so'z], 5-[so'z], 6-[so'z]||

Faqat post matnini yozing, boshqa izoh bermang.
"""
    text = _ask_gemini(prompt, max_tokens=2200)
    return {"type": "READING", "text": text}


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
    image_result = _generate_image(
        f"A beautiful, realistic photo-illustration capturing the mood of "
        f"{theme}, warm and inviting morning atmosphere, high quality"
    )
    return {"type": "GREETING", "text": text, **image_result}


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
        if "image_bytes" in result:
            print(f"IMAGE: {len(result['image_bytes'])} bayt (Gemini)")
        else:
            print("IMAGE (fallback URL):", result["image_url"])
        print()

    greeting = generate_daily_greeting("Monday")
    print("=== GREETING (Monday) ===")
    print(greeting["text"])
    if "image_bytes" in greeting:
        print(f"IMAGE: {len(greeting['image_bytes'])} bayt (Gemini)")
    else:
        print("IMAGE (fallback URL):", greeting["image_url"])
