"""
generate_content.py
--------------------
Kontentni generatsiya qilib, JSON faylga saqlaydi (keyingi "publish"
bosqichi buni o'qiydi) VA GitHub Actions'ning "Summary" sahifasiga
chiqaradi — shunda tasdiqlashdan oldin uni ko'rib chiqish mumkin.

Ishlatilishi:
    python generate_content.py vocabulary
    python generate_content.py grammar
    python generate_content.py idioms
    python generate_content.py reading
"""

import sys
import os
import json

from content_generator import (
    generate_vocabulary_post,
    generate_grammar_post,
    generate_idiom_post,
    generate_reading_test,
)

GENERATORS = {
    "vocabulary": generate_vocabulary_post,
    "grammar": generate_grammar_post,
    "idioms": generate_idiom_post,
    "reading": generate_reading_test,
}


def write_summary(post: dict):
    """GitHub Actions'ning 'Summary' sahifasiga ko'rib chiqish uchun yozadi."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(f"# 🔎 Tasdiqlashdan oldin ko'rib chiqing: {post['type']}\n\n")
        f.write(f"![illustration]({post['image_url']})\n\n")
        f.write("```\n")
        f.write(post["text"])
        f.write("\n```\n\n")
        f.write(
            "⬇️ Agar bu post SIFATLI va TO'G'RI bo'lsa — pastdagi "
            "'Review deployments' orqali tasdiqlang.\n"
            "Agar XATO yoki NOTO'G'RI bo'lsa — workflow'ni shunchaki "
            "rad eting yoki hech narsa qilmang (kanalga chiqmaydi).\n"
        )


if __name__ == "__main__":
    content_type = sys.argv[1] if len(sys.argv) > 1 else None
    if content_type not in GENERATORS:
        print(f"Xato: noto'g'ri kontent turi '{content_type}'. "
              f"Quyidagilardan birini tanlang: {list(GENERATORS.keys())}")
        sys.exit(1)

    post = GENERATORS[content_type]()

    # Keyingi bosqich (publish_content.py) o'qishi uchun saqlaymiz
    with open("content.json", "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)

    write_summary(post)
    print(f"✅ {post['type']} kontenti generatsiya qilindi va tekshirishga tayyor.")
