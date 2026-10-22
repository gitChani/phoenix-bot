import os
import re
import sys
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from firecrawl import FirecrawlApp

load_dotenv()

supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
firecrawl = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

# --- מגבלות בטיחות ---
MAX_PAGES_PER_CRAWL = 10      # קרדיט אחד לדף -> לכל היותר 10 קרדיטים לכתובת
CREDIT_BUDGET = 800           # מתוך 966; הסקריפט לא יתחיל אם ההערכה גבוהה מזה
GEMINI_DELAY = 0.05           # Tier 1: כמעט בלי השהיה (retry על 429 נשאר)
GEMINI_RETRIES = 3
MAX_DAILY_QUOTA = 10**9       # Tier 1: מבוטל בפועל
MIN_CHUNK_CHARS = 100
MAX_CHUNK_CHARS = 1500

URLS_TO_CRAWL = [
    "https://www.fnx.co.il/car-insurance/",
    "https://www.fnx.co.il/apartment-insurance/",
    "https://www.fnx.co.il/mortgage-insurance/",
    "https://www.fnx.co.il/life-insurance/",
    "https://www.fnx.co.il/disability-and-incapacity-to-work/",
    "https://www.fnx.co.il/health-insurance/",
    "https://www.fnx.co.il/pets-insurance/",
    "https://www.fnx.co.il/business-insurance/",
    "https://www.fnx.co.il/marine_aviation_insurance/",
    "https://www.fnx.co.il/savings/",
    "https://www.fnx.co.il/pension-savings/",  # לפני pensya-self-employee: הזחילה שלו אמורה לכסות אותו
    "https://www.fnx.co.il/gemel/",
    "https://www.fnx.co.il/ishtalmutfund/",
    "https://www.fnx.co.il/pension_retirement/",
    "https://www.fnx.co.il/takanottashlum/",
    "https://www.fnx.co.il/pension-savings/pensya-self-employee/",
    "https://www.fnx.co.il/claims-customer-service/",
]


def norm(url: str) -> str:
    return url.split("#")[0].split("?")[0].rstrip("/")


def split_text_to_chunks(text: str) -> list:
    # פסקאות קצרות (כותרת, מספר טלפון, "התחלת שיחה") לא נזרקות אלא מצטרפות לפסקה הבאה עד שהקטע מגיע לאורך מינימלי.
    # כותרות משנה (###) נשארות באותו קטע עם הכותרת שלפניהן (עד MAX_CHUNK_CHARS), כך שבלוק כמו "כל הדרכים לדבר איתנו" נשמר שלם עם כותרתו
    text = re.sub(r"!\[[^\]]*\]\(<Base64-Image-Removed>\)(\\)*", "", text)
    paras = [p.strip() for p in text.split("\n\n")]
    paras = [p for p in paras if p and p not in ("-", "\\")]
    chunks, buffer = [], []
    for i, para in enumerate(paras):
        buffer.append(para)
        joined = "\n\n".join(buffer)
        next_is_subsection = i + 1 < len(paras) and paras[i + 1].startswith("###")
        # לא חותכים אחרי כותרת או אחרי פסקה קצרה: רצף פסקאות קצרות (כמו בלוק פרטי קשר) נשאר קטע אחד, ונסגר בפסקה ארוכה
        hold = next_is_subsection or para.startswith("#") or len(para) <= MIN_CHUNK_CHARS
        if len(joined) > MIN_CHUNK_CHARS and (not hold or len(joined) > MAX_CHUNK_CHARS):
            chunks.append(joined)
            buffer = []
    if buffer:
        leftover = "\n\n".join(buffer)
        if chunks:
            chunks[-1] += "\n\n" + leftover
        elif len(leftover) > MIN_CHUNK_CHARS:
            chunks.append(leftover)
    return chunks


def embed_with_retry(chunk: str):
    for attempt in range(GEMINI_RETRIES):
        try:
            resp = gemini_client.models.embed_content(model="gemini-embedding-2", contents=chunk)
            return resp.embeddings[0].values
        except Exception as e:
            wait = 20 * (attempt + 1)
            print(f"  - שגיאת Gemini ({e}); מנסה שוב בעוד {wait} שניות")
            time.sleep(wait)
    return None


def save_page(page_url: str, title: str, chunks: list, state: dict) -> bool:
    """מחזיר False אם הגענו למכסה היומית."""
    # מחיקת גרסה קודמת של הדף כדי שהרצה חוזרת תעדכן ולא תכפיל
    supabase.table("documents").delete().eq("metadata->>url", page_url).execute()
    saved = 0
    for chunk in chunks:
        if state["embeds"] >= MAX_DAILY_QUOTA:
            print("\n[עצירת חירום] הגענו למגבלת המכסה היומית!")
            return False
        vector = embed_with_retry(chunk)
        state["embeds"] += 1
        time.sleep(GEMINI_DELAY)
        if vector is None:
            continue
        try:
            supabase.table("documents").insert({
                "content": chunk,
                "embedding": vector,
                "metadata": {"url": page_url, "title": title},
            }).execute()
            saved += 1
        except Exception as e:
            print(f"  - דילוג על מקטע (שגיאת שמירה): {e}")
    print(f"  V נשמרו {saved}/{len(chunks)} מקטעים. בקשות Gemini עד כה: {state['embeds']}")
    return True


def run_crawler(dry_run: bool = False):
    estimate = len(URLS_TO_CRAWL) * MAX_PAGES_PER_CRAWL
    print(f"הערכת קרדיטים מקסימלית ל-Firecrawl: {estimate} (תקציב {CREDIT_BUDGET}, יתרה 966)")
    if estimate > CREDIT_BUDGET:
        print("ההערכה חורגת מהתקציב - הקטיני MAX_PAGES_PER_CRAWL. יוצאת.")
        return
    if dry_run:
        print("dry-run: לא בוצעה זחילה.")
        return

    state = {"embeds": 0}
    seen_pages = set()
    credits_used = 0

    for base_url in URLS_TO_CRAWL:
        if norm(base_url) in seen_pages:
            print(f"\n[דילוג] {base_url} כבר נסרק כחלק מזחילה קודמת (חוסך קרדיטים)")
            continue
        print(f"\n[מתחיל זחילה] {base_url}")

        try:
            result = firecrawl.crawl_url(
                base_url,
                params={"limit": MAX_PAGES_PER_CRAWL, "scrapeOptions": {"formats": ["markdown"]}},
            )
            pages = result.get("data", []) if isinstance(result, dict) else getattr(result, "data", [])
        except Exception as e:
            print(f"[שגיאה] זחילה נכשלה ב-{base_url}: {e}")
            continue

        credits_used += len(pages)
        print(f"נמצאו {len(pages)} דפים (קרדיטים משוערים עד כה: {credits_used})")

        for page in pages:
            if not isinstance(page, dict):
                page = getattr(page, "__dict__", {})
            meta = page.get("metadata") or {}
            if not isinstance(meta, dict):
                meta = getattr(meta, "__dict__", {})
            page_url = meta.get("sourceURL") or meta.get("source_url") or meta.get("url") or base_url
            title = meta.get("title") or page_url
            key = norm(page_url)
            if key in seen_pages:
                continue
            seen_pages.add(key)

            chunks = split_text_to_chunks(page.get("markdown") or "")
            if not chunks:
                continue
            print(f"[מעבד] {page_url} ({len(chunks)} מקטעים)")
            if not save_page(page_url, title, chunks, state):
                return

        print("ממתין 5 שניות לפני הכתובת הבאה...")
        time.sleep(5)

    print(f"\n[סיום] הושלם. קרדיטים משוערים: {credits_used}, בקשות Gemini: {state['embeds']}")


if __name__ == "__main__":
    run_crawler(dry_run="--dry-run" in sys.argv)
