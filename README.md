# Telegram Kanal uchun Avtomatik Kontent Bot (GitHub Actions + Tasdiqlash)

Bu versiya **hech qanday server yoki doimiy ishlaydigan kompyuter talab
qilmaydi** VA **tasdiqlash bosqichini** o'z ichiga oladi — GitHub'ning
o'zi bu funksiyani bepul beradi (agar repository PUBLIC bo'lsa).

## Bu qanday ishlaydi

Har bir post 2 bosqichda amalga oshadi:

1. **GENERATE** — belgilangan vaqtda GitHub avtomatik ravishda kontent
   (matn + rasm) generatsiya qiladi va uni "Summary" sahifasiga chiqaradi
2. **KUTISH** — workflow shu yerda **to'xtaydi** va sizga GitHub orqali
   bildirishnoma keladi ("Deployment review kerak")
3. **TASDIQLASH** — siz kontentni ko'rib chiqasiz, agar to'g'ri bo'lsa
   "Approve" tugmasini bosasiz
4. **PUBLISH** — faqat shundan keyin post kanalga chiqadi

Faqat **kunlik salomlashish** (07:00) bundan mustasno — u avtomatik,
tasdiqlashsiz chiqaveradi (xato bo'lish xavfi juda past bo'lgani uchun).

## MUHIM: Repository PUBLIC bo'lishi kerak

GitHub'ning "tasdiqlash talab qilish" funksiyasi (required reviewers)
faqat **ochiq (public)** repositorylarda bepul. Bu xavfsiz — chunki:
- Sizning API kalitlaringiz kodda emas, GitHub Secrets'da saqlanadi
  (Secrets hech qachon, hech kimga ko'rinmaydi, hatto repo ochiq bo'lsa ham)
- Kodning o'zi (grammar/vocab generatsiya qiluvchi skript) maxfiy emas

## Fayllar tuzilishi

```
├── content_generator.py       # Matn va rasm generatsiya qiluvchi funksiyalar
├── telegram_sender.py         # Kanalga yuborish funksiyasi
├── generate_content.py        # 1-bosqich: kontent yaratish (parametrli)
├── publish_content.py         # 2-bosqich: tasdiqlangandan keyin yuborish
├── post_greeting.py           # Kunlik salomlashish (alohida, tasdiqlashsiz)
├── requirements.txt
└── .github/
    └── workflows/
        ├── greeting.yml       # 07:00 — avtomatik (1 bosqich)
        ├── vocabulary.yml     # 09:00 — tasdiqlash bilan (2 bosqich)
        ├── grammar.yml        # 12:00 — tasdiqlash bilan (2 bosqich)
        ├── idioms.yml         # 15:00 — tasdiqlash bilan (2 bosqich)
        └── reading.yml        # 20:00 — tasdiqlash bilan (2 bosqich)
```

## O'rnatish qadamlari

### 1. GitHub'da PUBLIC repository yarating

Repository yaratishda **"Public"** ni tanlang (Private emas!).

### 2. Barcha fayllarni yuklang

`.github/workflows/` papkasi tuzilishi bilan birga yuklanishi kerak
(tavsiya: GitHub Desktop dasturidan foydalaning, chunki veb-brauzer
orqali nuqta bilan boshlangan papkalarni yuklash qiyinroq).

### 3. "production" Environment yarating va tasdiqlovchini belgilang

1. Repository → **Settings** → **Environments** → **New environment**
2. Nomi: aynan **`production`** deb yozing (workflow fayllaridagi nom
   bilan mos kelishi shart)
3. **"Required reviewers"** katagini belgilang
4. O'zingizning GitHub akkountingizni (yoki hamkasbingizni) reviewer
   sifatida qo'shing
5. Saqlang

### 4. Secrets qo'shing

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`:

| Nomi | Qiymati |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan olingan token |
| `GEMINI_API_KEY` | aistudio.google.com/apikey'dan olingan bepul kalit |
| `CHANNEL_ID` | `@sizning_kanalingiz` |

### 5. Botni kanalga admin qilib qo'shing

Kanal sozlamalari → Administratorlar → Admin qo'shish → botingiz →
"Post yuborish" huquqini yoqing.

### 6. Bildirishnomalarni yoqing (juda muhim!)

Tasdiqlash so'rovi kelganda darhol bilishingiz uchun:
- GitHub mobil ilovasini o'rnating (App Store / Google Play) va
  push-bildirishnomalarni yoqing, YOKI
- GitHub email bildirishnomalarini yoqib qo'ying (Settings →
  Notifications)

### 7. Sinab ko'ring

1. Repository → **Actions** → "Vocabulary Post" workflow'ini tanlang
2. **"Run workflow"** tugmasini bosing
3. Bir necha soniyadan keyin workflow "generate" bosqichini tugatadi
4. Sizga bildirishnoma keladi: "Review deployments"
5. Workflow run sahifasiga kiring, **"Review deployments"** tugmasini
   bosing, generatsiya qilingan kontentni (Summary'da) ko'ring
6. Agar to'g'ri bo'lsa — **"Approve and deploy"** bosing
7. Kanalingizni tekshiring — post chiqqan bo'lishi kerak

## Agar noto'g'ri kontent chiqsa

"Review deployments" oynasida **"Reject"** tugmasini bosing — post
kanalga umuman chiqmaydi. Workflow shu yerda to'xtaydi, hech qanday
xato oqibat bermaydi.

## Vaqtni o'zgartirish

Tegishli `.yml` faylidagi `cron` qatorini o'zgartiring (UTC vaqtida,
Toshkentdan 5 soat ayirib hisoblang).
