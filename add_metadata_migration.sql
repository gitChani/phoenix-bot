-- מריצים ב-Supabase -> SQL Editor
-- 1. עמודת metadata לשמירת ה-URL של כל קטע
alter table documents add column if not exists metadata jsonb default '{}'::jsonb;

-- 2. הנתונים הקיימים ללא URL - מנקים וטוענים מחדש עם add_website_data.py
truncate table documents;

-- 3. עדכון match_documents כך שיחזיר גם metadata.
-- חשוב: הפונקציה הקיימת לא נמצאת ב-repo. לפני ההרצה בדקי את הגדרתה:
--   select pg_get_functiondef('match_documents'::regproc);
-- ואת ממד הווקטור (VECTOR_DIM למטה) בהתאם לעמודה documents.embedding.
drop function if exists match_documents(vector, float, int);

create or replace function match_documents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (id bigint, content text, metadata jsonb, similarity float)
language sql stable
as $$
  select d.id, d.content, d.metadata, 1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  where 1 - (d.embedding <=> query_embedding) > match_threshold
  order by d.embedding <=> query_embedding
  limit match_count;
$$;
