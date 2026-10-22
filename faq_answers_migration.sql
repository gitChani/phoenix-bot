-- מריצים ב-Supabase -> SQL Editor
-- טבלה לשמירת תשובות מוכנות לשאלות הנפוצות (המפתח הוא נוסח השאלה המדויק)
create table if not exists faq_answers (
  question text primary key,
  answer text not null,
  sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
