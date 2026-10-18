import os
from dotenv import load_dotenv
from supabase import create_client, Client

# טעינת המשתנים מהקובץ .env
load_dotenv()

# שליפת כתובת השרת והמפתח
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# יצירת החיבור למסד הנתונים
supabase: Client = create_client(url, key)

# בדיקת החיבור: ניסיון לשלוף נתונים מהטבלה הריקה שלנו
try:
    response = supabase.table("documents").select("*").execute()
    print("✅ Connection successful!")
    print("Data in table:", response.data)
except Exception as e:
    print("❌ Connection failed:")
    print(e)