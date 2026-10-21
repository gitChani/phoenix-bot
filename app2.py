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

# תצוגת היסטוריית השיחה
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

                # ב. חיפוש במסד הנתונים - עודכן לפרמטרים מחמירים לדיוק מקסימלי
                search_response = supabase.rpc(
                    "match_documents",
                    {"query_embedding": question_vector, "match_threshold": 0.78, "match_count": 8}
                ).execute()

                # ג. ניסוח תשובה מבוססת מקורות עם פרומפט קשוח באנגלית למניעת הזיות
                if len(search_response.data) > 0:
                    context = "\n\n".join([doc['content'] for doc in search_response.data])
                    
                    ai_prompt = f"""You are an official, professional, and courteous digital customer service representative for 'The Phoenix' (הפניקס) insurance company.
Your role is to assist customers and provide clear, accessible information.

STRICT RULES:
1. Base your answer EXCLUSIVELY on the information provided under 'Company Data'. Do NOT hallucinate, guess, or invent any coverages, policies, or facts.
2. If the answer to the user's question is not explicitly found in the 'Company Data', or if the user asks about competitor companies, you MUST politely refuse by answering EXACTLY with this Hebrew phrase: "מצטער, אין לי מידע מדויק על כך. אנא פנה לשירות הלקוחות של הפניקס".
3. NEVER use meta-phrases like "Based on the provided context", "According to the text", or "The document says". Act naturally as the company's representative.
4. Use bullet points when presenting a list of options, coverages, or steps.
5. You MUST generate your final response in HEBREW ONLY.

Company Data:
{context}

User Question: {prompt}"""
                    
                    # שימוש במודל 2.5 המהיר והמדויק
                    answer_response = gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=ai_prompt
                    )
                    final_answer = answer_response.text
                else:
                    # שינינו גם כאן את משפט ברירת המחדל שיתאים לחוקים של הפרומפט
                    final_answer = "מצטער, אין לי מידע מדויק על כך. אנא פנה לשירות הלקוחות של הפניקס."

                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})

            except Exception as e:
                st.error("אירעה שגיאה זמנית במערכת.")
                print(f"Error: {e}")