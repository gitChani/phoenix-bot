# chunker.py

def chunk_text(text, max_length=800):
    # מפריד את הטקסט לפי פסקאות (שורה ריקה בין פסקה לפסקה)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        # אם הוספת הפסקה לא חורגת מהגודל המקסימלי, נוסיף אותה לקטע הנוכחי
        if len(current_chunk) + len(p) < max_length:
            current_chunk += p + "\n\n"
        else:
            # אם חרגנו, שומרים את הקטע הקיים ומתחילים קטע חדש
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    
    # שמירת הקטע האחרון שנשאר בזיכרון
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

# 1. קריאת הטקסט מהקובץ ששמרנו בשלב הקודם
try:
    with open("scraped_page.md", "r", encoding="utf-8") as file:
        full_text = file.read()
        
    # 2. חיתוך הטקסט לקטעים
    my_chunks = chunk_text(full_text)

    # 3. הדפסת התוצאות למסך כדי לבדוק שהכל עובד
    print(f"הטקסט מהאתר חולק בהצלחה ל-{len(my_chunks)} קטעים.")
    print("\n--- דוגמה לקטע הראשון ---")
    print(my_chunks[0])
    print("\n--- דוגמה לקטע השני ---")
    print(my_chunks[1])

except FileNotFoundError:
    print("הקובץ scraped_page.md לא נמצא. ודאי שהרצת את scraper.py בהצלחה קודם לכן.")