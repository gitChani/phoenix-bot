import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

# הגדרות עמוד מקצועיות (ללא אש)
st.set_page_config(page_title="הפניקס - נציג דיגיטלי", page_icon="🏢", layout="centered")

# עיצוב מתקדם לממשק
st.markdown("""
    <style>
    * { direction: rtl; font-family: sans-serif; }
    .stTextInput > div > div > input { 
        direction: rtl; 
        border-radius: 10px;
    }
    .stChatMessage { 
        border-radius: 10px; 
        padding: 10px; 
        margin-bottom: 10px; 
        border: 1px solid #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

# בדיקה אם קובץ הלוגו קיים, אם כן מציג אותו, אחרת כותרת רגילה
assistant_avatar = "logo.png" if os.path.exists("logo.png") else "🏢"

if os.path.exists("logo.png"):
    # יישור הלוגו למרכז
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
else:
    st.title("הפניקס - שירות דיגיטלי")

st.caption("ברוכים הבאים! אני הנציג הדיגיטלי של הפניקס. למדתי הרגע את נתוני החברה, במה אוכל לעזור?")

# טעינת משתנים וחיבורים
load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

if "messages" not in st.session_state:
    st.session_state.messages = []

# תצוגת היסטוריית השיחה (עם האייקון המעודכן לבוט)
for msg in st.session_state.messages:
    avatar = assistant_avatar if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("הקלידו את השאלה שלכם כאן..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("מחפש מידע במאגרי החברה..."):
            try:
                # א. הפיכת השאלה לווקטור
                embed_response = gemini_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=prompt
                )
                question_vector = embed_response.embeddings[0].values

                # ב. חיפוש במסד הנתונים
                search_response = supabase.rpc(
                    "match_documents",
                    {"query_embedding": question_vector, "match_threshold": 0.5, "match_count": 6}
                ).execute()

                # ג. ניסוח תשובה מבוססת מקורות
                if len(search_response.data) > 0:
                    # איחוד של המקטעים שנמצאו
                    context = "\n".join([doc['content'] for doc in search_response.data])
                    ai_prompt = f"אתה נציג שירות רשמי של חברת הפניקס. מבוסס אך ורק על המידע הבא: '{context}', ענה בצורה מקצועית ואדיבה על השאלה: {prompt}. אם התשובה לא נמצאת בטקסט, אמור במדויק 'לצערי אין לי מידע על כך כרגע'."
                    
                    answer_response = gemini_client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=ai_prompt
                    )
                    final_answer = answer_response.text
                else:
                    final_answer = "מצטער, לא מצאתי מידע רלוונטי לשאלה זו במאגרי החברה."

                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})

            except Exception as e:
                st.error("אירעה שגיאה זמנית במערכת.")
                print(f"Error: {e}")