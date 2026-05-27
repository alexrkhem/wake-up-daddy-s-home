# 🎵 Jarvis Personal Dashboard

> A local-first personal OS with an indie record shop aesthetic.
> Built with Python + Streamlit. Tunnels to your phone via ngrok.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. First-time setup (creates .env, initializes DB)
python setup.py

# 3. Add your API key
#    Open .env and set: ANTHROPIC_API_KEY=sk-ant-...

# 4. Run
streamlit run app.py        # or double-click run.bat (Windows)

# 5. Access on your phone
python tunnel.py            # requires NGROK_AUTH_TOKEN in .env
```

---

## What's Inside

| Page | Features |
|------|----------|
| 🏠 Home | Overview dashboard — all modules at a glance |
| 📋 Todo | Tasks with priority, due dates, status tracking |
| 📅 Calendar | Google Calendar integration — view & add events |
| 😴 Sleep | Sleep log, quality tracking, routine checklist, charts |
| 💪 Fitness | Weightlifting log, steps, height training, physique photos, supplements |
| 🍎 Nutrition | Cronometer CSV import, macro tracking, eating schedule |
| 🎵 Music | Guitar + euphonium session logging, streaks, goals |
| 📚 Academics | Courses, assignments, study sessions, AI tutor with RAG |
| 📈 Investments | Portfolio (yfinance), watchlist, research notes, petrodollar thesis |
| 🎨 Design | Project tracker, file manager, EDP planner, timeline |
| 📓 Journal | Daily journal, win log, lessons learned, mood tracker |

**Jarvis AI** is available in the sidebar on every page. Uses Anthropic Claude.

---

## Setup Details

### Environment Variables (`.env`)
```env
ANTHROPIC_API_KEY=sk-ant-...       # Required for Jarvis AI & Academic tutor
NGROK_AUTH_TOKEN=your-token        # Required for phone tunneling (free at ngrok.com)
GOOGLE_CALENDAR_ENABLED=true       # Optional — see GOOGLE_CALENDAR_SETUP.md
```

### File Storage
- **Database:** `data/dashboard.db` (SQLite — all your data)
- **Photos:** `photos/` (physique progress photos)
- **Uploads:** `uploads/` (textbooks, temp files)
- **Project files:** `C:/Dashboard_Files/` on Windows, `~/Dashboard_Files/` on Mac/Linux
  - These persist on your hard drive permanently, even if you move the app

### Google Calendar
See `GOOGLE_CALENDAR_SETUP.md` for the full 6-step setup guide.

### AI Tutor (RAG)
1. Go to **📚 Academics → AI Tutor**
2. Upload a PDF textbook → Click "Index Textbook"
3. Select the textbook and ask Jarvis questions or generate practice problems
4. Works best with STEM textbooks (Linear Algebra, Statics, Chemistry, etc.)

### Cronometer Nutrition Import
1. In Cronometer (web): **Diary → Export → Daily Nutrition CSV**
2. Go to **🍎 Nutrition → Import Cronometer CSV**
3. Upload the file — columns are auto-detected
4. Click Import — data is saved to your dashboard

---

## Phone Access (ngrok Tunnel)

1. Get a free account at [ngrok.com](https://ngrok.com)
2. Copy your auth token → add to `.env`: `NGROK_AUTH_TOKEN=...`
3. Run: `python tunnel.py`
4. Open the printed URL on your phone — bookmark it

The tunnel stays active as long as `tunnel.py` is running.
The URL changes each restart (free tier). Upgrade ngrok for a static URL.

---

## Tech Stack

- **UI:** Streamlit 1.35+
- **AI:** Anthropic Claude (claude-sonnet-4)
- **RAG:** LangChain + ChromaDB + PyPDF
- **Market Data:** yfinance
- **Calendar:** Google Calendar API v3
- **Database:** SQLite (local, no server needed)
- **Tunnel:** pyngrok
- **Charts:** Plotly

---

## Aesthetic

Warm vintage cream `#f0e6d3` · Vinyl black `#1a1814` · Vintage orange `#d4681e`
Sage green `#7a8c6e` · Worn gold `#c4a882` · Playfair Display + Space Mono

*Inspired by indie record shops, analog gear, and the feel of a well-worn album sleeve.*

---

## Data Privacy

Everything runs locally on your machine. No data leaves your computer except:
- Jarvis AI chat → Anthropic API (your messages)
- Google Calendar → Google's servers (your existing calendar data)
- yfinance market data → Yahoo Finance (ticker symbols only, read-only)
- ngrok tunnel → ngrok servers (proxies traffic, no data stored)
