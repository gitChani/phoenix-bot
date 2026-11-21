# Pini — RAG Digital Assistant for The Phoenix

An end-to-end Retrieval-Augmented Generation (RAG) web assistant in Hebrew built for **The Phoenix** (`fnx.co.il`), developed during an Open Code AI Hackathon. Pini answers customer questions strictly grounded in official website content, streams responses in real time, caches frequent answers, and provides contextual insurance & savings glossary tooltips.

**Live Demo:** https://phoenix-bot-cnwba6ntz228n4smyrewvh.streamlit.app/

---

## Key Features

- **Grounded RAG Pipeline:** Converts queries into embeddings (`gemini-embedding-2`), performs similarity search in Supabase (`pgvector` via `match_documents`), deduplicates/filters low-signal chunks, and generates answers using `gemini-3.8-flash` with strict source-grounding rules and refusal handling.
- **Follow-up Query Rewriting:** Rewrites contextual follow-up messages into standalone search queries (`standalone_question`) so multi-turn conversations retrieve accurate documents without losing context.
- **FAQ Sidebar & Persistent DB Cache:** Organized FAQ tabs and topic accordions in the sidebar, backed by both in-memory caching (`@st.cache_resource`) and a persistent `faq_answers` table in Supabase (`faq_answers_migration.sql`).
- **Interactive Glossary Tooltips:** Highlights the first occurrence of financial and insurance terms from `glossary.json` (with built-in fallbacks and aliases) and displays hover/click/tap definitions dynamically positioned in the viewport.
- **Streaming UX & Guardrails:** Smooth streaming with retry logic for transient `503` errors, source attribution (`[[USED: ...]]` / `[[NO_SOURCES]]`), send-lock protection while generating, auto-scroll that yields when the user scrolls up, and mobile sidebar auto-collapse.
- **Budget-Aware Data Ingestion (`add_website_data2.py`):** Crawls selected `fnx.co.il` sections with Firecrawl (`--dry-run` support, credit budget check, URL normalization, deduplication), chunks markdown while keeping headings/short blocks intact, embeds chunks, and replaces stale records per URL before inserting.

---

## Tech Stack

- **Frontend / UI:** Streamlit, custom RTL CSS (`Heebo`), embedded JS helpers
- **LLM & Embeddings:** Google GenAI SDK (`gemini-3.8-flash`, `gemini-embedding-2`)
- **Vector Database & Persistence:** Supabase (`pgvector`, `match_documents` RPC, `documents` & `faq_answers` tables)
- **Web Ingestion:** Firecrawl (`FirecrawlApp`)
- **Configuration & Utilities:** `python-dotenv`, `requests`, SQL migrations

---

## Project Structure

- `app.py` — Main Streamlit chat application, RAG orchestration, streaming, FAQ cache, glossary tooltips, and UI helpers.
- `add_website_data2.py` — Budget-checked Firecrawl crawler, markdown chunker, Gemini embedder, and idempotent Supabase `documents` loader.
- `glossary.json` — Insurance, pension, and savings glossary definitions.
- `faq_answers_migration.sql` — SQL schema for caching FAQ responses and sources in Supabase.
- `add_metadata_migration.sql` — SQL migration for document metadata.
- `ask_bot.py`, `chunker.py`, `embedder.py`, `check_models.py`, `list_models.py`, `test_connection.py` — Standalone development and verification scripts from building and testing the pipeline.
- `.env.example` — Template for required environment variables.
- `requirements.txt` — Core runtime dependencies.

---

## Setup & Running Locally

1. Clone the repository:
   git clone https://github.com/gitChani/phoenix-bot.git
   cd phoenix-bot

2. Install dependencies:
   pip install -r requirements.txt
   (If you run the crawler/ingestion scripts locally, also install firecrawl-py and requests if not already in your environment.)

3. Configure environment variables:
   Copy .env.example to .env and fill in your keys:
   GEMINI_API_KEY=your_gemini_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key

4. Prepare Supabase:
   Run your SQL migrations (including faq_answers_migration.sql and metadata setup) and ensure the documents table and match_documents RPC function are configured.

5. Ingest website data (optional / when refreshing knowledge base):
   python add_website_data2.py --dry-run
   python add_website_data2.py

6. Run the app:
   streamlit run app.py

---

## Disclaimer

Answers are generated from publicly available Phoenix website content for informational purposes only and do not constitute insurance, financial, legal, medical, or personalized advisory services.
