import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

# 1. טעינת המשתנים מהקובץ .env
load_dotenv()

# 2. התחברות ל-Supabase
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_KEY")
)

# 3. התחברות לג'מיני
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# הטקסט שאנחנו רוצים לשמור
text_to_save = "הפניקס (עוף החול) הוא ציפור אש מיתולוגית שקמה לתחייה מהאפר של עצמה, ומסמלת התחדשות ונצחיות."

try:
    # 4. יצירת ההטמעה (Vector) בעזרת המודל המעודכן
    print("Generating embedding with Gemini...")
    response = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text_to_save
    )
    
    # חילוץ הווקטור מתוך התשובה
    vector = response.embeddings[0].values

    # 5. שמירת הטקסט והווקטור ב-Supabase
    print("Saving to Supabase...")
    supabase.table("documents").insert({
        "content": text_to_save,
        "embedding": vector
    }).execute()

    print("✅ הנתונים נשמרו בהצלחה במסד הנתונים!")
    
except Exception as e:
    print("❌ שגיאה התרחשה:")
    print(e)