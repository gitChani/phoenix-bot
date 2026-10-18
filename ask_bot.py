import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

# 1. טעינת משתנים
load_dotenv()

# 2. חיבורים לשרתים
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 3. השאלה שאנחנו רוצים לשאול את הבוט
question = "מה זה עוף החול ומה הוא מסמל?"

try:
    # 4. הפיכת השאלה לווקטור בעזרת ג'מיני
    print("הופך את השאלה לווקטור...")
    embed_response = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=question
    )
    question_vector = embed_response.embeddings[0].values

    # 5. חיפוש ב-Supabase בעזרת הפונקציה שיצרנו
    print("מחפש מידע רלוונטי בזיכרון של הבוט...")
    search_response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": question_vector,
            "match_threshold": 0.5, # רמת התאמה מינימלית
            "match_count": 1 # נבקש רק את התוצאה הכי מתאימה
        }
    ).execute()

    # בודקים אם הפונקציה מצאה משהו
    if len(search_response.data) > 0:
        context = search_response.data[0]['content']
        print(f"✅ נמצא מידע רלוונטי במסד הנתונים: {context}\n")
        
        # 6. יצירת תשובה שוטפת בעזרת מודל הטקסט של ג'מיני (המודל המעודכן)
        print("מייצר תשובה חכמה...")
        prompt = f"מבוסס אך ורק על המידע הבא: '{context}', ענה בקצרה על השאלה: {question}"
        
        answer_response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        
        print("\n🤖 תשובת הפניקס-בוט:")
        print(answer_response.text)
        
    else:
        print("❌ לא מצאתי מידע רלוונטי בזיכרון לשאלה הזו.")

except Exception as e:
    print("❌ שגיאה התרחשה:")
    print(e)