import os
import requests
from dotenv import load_dotenv

# טעינת המפתח
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("בודק מול השרת אילו מודלים זמינים לחשבון שלך...")

# פנייה לשרת כדי לקבל את רשימת כל המודלים המורשים למפתח הזה
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
data = response.json()

print("\n--- מודלי הטמעה (Embeddings) שפתוחים עבורך ---")
found = False

# עוברים על כל המודלים ומדפיסים רק את אלו שתומכים ביצירת וקטורים
if 'models' in data:
    for model in data['models']:
        # בודקים אם המודל תומך בפעולת embedContent
        if 'embedContent' in model.get('supportedGenerationMethods', []):
            print(model['name'])
            found = True

if not found:
    print("שגיאה: לא נמצאו מודלי הטמעה זמינים למפתח הזה כלל.")
    print("פלט השרת המלא:", data)