import os
import requests
from dotenv import load_dotenv

# טעינת קובץ הסודות
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

sample_text = "עד 45% הנחה בביטוח המקיף למצטרפים חדשים"
print("שולח את הטקסט ישירות לשרת של Gemini...")

# פנייה לכתובת עם המודל המדויק שפתוח לחשבון שלך
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={api_key}"

payload = {
    "model": "models/gemini-embedding-2",
    "content": {
        "parts": [{"text": sample_text}]
    }
}

# שליחת הבקשה
response = requests.post(url, json=payload)
result = response.json()

# בדיקה האם קיבלנו את הווקטור בחזרה
if "embedding" in result:
    vector = result["embedding"]["values"]
    print(f"הטקסט הומר בהצלחה לווקטור המכיל {len(vector)} מספרים!")
    print("הנה 5 המספרים הראשונים מתוכו (כדי שתראי איך זה נראה):")
    print(vector[:5])
else:
    print("התקבלה שגיאה מהשרת:")
    print(result)