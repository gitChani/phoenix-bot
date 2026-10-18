import os
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# טעינת המפתח מקובץ הסודות
load_dotenv()
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

url = "https://www.fnx.co.il/car-insurance/"

print("מתחיל לסרוק את העמוד...")
scraped_data = app.scrape_url(url)

# חילוץ הטקסט הנקי מתוך האובייקט שחזר
text_content = scraped_data.markdown

# שמירת הטקסט לתוך קובץ חדש כדי לראות את העברית ישר
with open("scraped_page.md", "w", encoding="utf-8") as file:
    file.write(text_content)

print("הסריקה הסתיימה בהצלחה! התוכן נשמר בקובץ scraped_page.md")