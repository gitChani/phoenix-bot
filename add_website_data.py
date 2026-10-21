import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from firecrawl import FirecrawlApp

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
firecrawl_app = FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY"))

# הרשימה המלאה של עמודי הפניקס (ללא ויקיפדיה)
urls_to_scrape = [
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
    "https://www.fnx.co.il/pension-savings/",
    "https://www.fnx.co.il/gemel/",
    "https://www.fnx.co.il/ishtalmutfund/",
    "https://www.fnx.co.il/pension_retirement/",
    "https://www.fnx.co.il/takanottashlum/",
    "https://www.fnx.co.il/pension-savings/pensya-self-employee/",
    "https://www.fnx.co.il/claims-customer-service/"
]

# האם עמודת metadata קיימת בטבלה (נוספת במיגרציה add_metadata_migration.sql)
try:
    supabase.table("documents").select("metadata").limit(1).execute()
    HAS_METADATA = True
except Exception:
    HAS_METADATA = False
print("שומר URL ב-metadata" if HAS_METADATA else "עמודת metadata לא קיימת - שומר ללא URL")

print(f"מתחילים שאיבת נתונים מ-{len(urls_to_scrape)} עמודים באתר הפניקס...")

for url in urls_to_scrape:
    print(f"\nסורק את: {url}")
    try:
        scrape_result = firecrawl_app.scrape_url(url)
        text_content = scrape_result.markdown if hasattr(scrape_result, 'markdown') else str(scrape_result)
        
        # סינון: שומר רק פסקאות שיש בהן תוכן ממשי (מעל 100 תווים)
        chunks = [chunk.strip() for chunk in text_content.split('\n\n') if len(chunk.strip()) > 100]
        
        page_meta = getattr(scrape_result, 'metadata', None)
        page_title = (page_meta.get('title') if isinstance(page_meta, dict) else getattr(page_meta, 'title', None)) or url

        print(f"נמצאו {len(chunks)} פסקאות מידע. שומר במסד הנתונים...")

        # מניעת כפילויות בהרצות חוזרות (אפשרי רק כשיש עמודת metadata)
        if HAS_METADATA:
            supabase.table("documents").delete().eq("metadata->>url", url).execute()

        for i, chunk in enumerate(chunks):
            try:
                embed_response = gemini_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=chunk
                )
                vector = embed_response.embeddings[0].values
                
                row = {"content": chunk, "embedding": vector}
                if HAS_METADATA:
                    row["metadata"] = {"url": url, "title": page_title}
                supabase.table("documents").insert(row).execute()
            except Exception as inner_e:
                print(f"  - דילוג על מקטע (שגיאת שמירה): {inner_e}")
                
        # השהייה קלה של 2 שניות בין עמוד לעמוד כדי לא להעמיס על השרתים של הפניקס ולמנוע חסימה
        time.sleep(2)
            
    except Exception as e:
        print(f"❌ שגיאה בסריקת {url}: {e}")

print("\n🎉 סיימנו! הבוט טעון בכל המידע הרשמי של חברת הפניקס.")