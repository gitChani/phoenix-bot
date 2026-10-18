import os
from dotenv import load_dotenv
from google import genai

# טעינת המפתח מתוך קובץ ה-.env
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

# חיבור לג'מיני
client = genai.Client(api_key=api_key)

print("🔍 שואל את גוגל אילו מודלים של הטמעות זמינים לך...")

try:
    # שליפת כל המודלים הזמינים למפתח הזה
    models = client.models.list()
    found = False
    
    for m in models:
        # סינון רק של מודלים שקשורים ל-embedding
        if "embed" in m.name.lower():
            print(f"✅ נמצא מודל זמין: {m.name}")
            found = True
            
    if not found:
        print("❌ לא נמצאו מודלי הטמעות בכלל עבור המפתח הזה.")
        
except Exception as e:
    print(f"שגיאה בגישה למודלים: {e}")