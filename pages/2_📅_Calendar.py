import streamlit as st, sys, datetime, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Calendar · Jarvis", page_icon="📅", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from config import CREDENTIALS_FILE, TOKEN_FILE, GOOGLE_CALENDAR_SCOPES
init_db(); apply_styles(); render_jarvis_sidebar()

page_header("📅", "Google Calendar", "events & schedule")

# ── Google Auth ──────────────────────────────────────────────────────────────
def get_calendar_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GOOGLE_CALENDAR_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    return None, "no_credentials"
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), GOOGLE_CALENDAR_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(str(TOKEN_FILE), "w") as f:
                f.write(creds.to_json())
        return build("calendar", "v3", credentials=creds), "ok"
    except Exception as e:
        return None, str(e)

if not CREDENTIALS_FILE.exists():
    st.warning("⚠ **credentials.json not found.** See the **GOOGLE_CALENDAR_SETUP.md** file in your dashboard folder for step-by-step setup instructions.")
    with st.expander("Quick Setup Checklist"):
        st.markdown("""
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Google Calendar API**
3. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
4. Application type: **Desktop App**
5. Download JSON → rename to `credentials.json` → place in your dashboard folder
6. Add your Google account as a **Test User** under OAuth consent screen
7. Restart the dashboard — a browser window will open to authorize
""")

tab_view, tab_add = st.tabs(["📆  Upcoming Events", "＋  Add Event"])

with tab_view:
    if st.button("🔄 Refresh Calendar"):
        st.session_state.pop("cal_events", None)

    if "cal_events" not in st.session_state:
        with st.spinner("Connecting to Google Calendar…"):
            service, status = get_calendar_service()
            if service:
                now = datetime.datetime.utcnow().isoformat() + "Z"
                end = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + "Z"
                try:
                    result = service.events().list(
                        calendarId="primary", timeMin=now, timeMax=end,
                        maxResults=30, singleEvents=True, orderBy="startTime"
                    ).execute()
                    st.session_state.cal_events = result.get("items", [])
                    st.session_state.cal_status = "ok"
                except Exception as e:
                    st.session_state.cal_events = []
                    st.session_state.cal_status = str(e)
            else:
                st.session_state.cal_events = []
                st.session_state.cal_status = status

    events = st.session_state.get("cal_events", [])
    cal_status = st.session_state.get("cal_status", "")

    if cal_status not in ("ok", "") and not events:
        st.error(f"Calendar error: {cal_status}")
    elif not events:
        st.info("No upcoming events in the next 30 days, or calendar not yet connected.")
    else:
        # Group by date
        grouped = {}
        for ev in events:
            start = ev.get("start", {})
            date_str = start.get("date") or start.get("dateTime", "")[:10]
            grouped.setdefault(date_str, []).append(ev)

        today_str = str(datetime.date.today())
        for date_str in sorted(grouped.keys()):
            try:
                d = datetime.date.fromisoformat(date_str)
                is_today = date_str == today_str
                label_color = "#d4681e" if is_today else "#c4a882"
                label = d.strftime("%A, %B %-d") + (" ← TODAY" if is_today else "")
            except Exception:
                label = date_str
                label_color = "#c4a882"

            st.markdown(f'<div class="label-mono" style="color:{label_color};margin-top:1rem">{label}</div>', unsafe_allow_html=True)
            for ev in grouped[date_str]:
                start_info = ev.get("start", {})
                time_str = ""
                if "dateTime" in start_info:
                    try:
                        dt = datetime.datetime.fromisoformat(start_info["dateTime"].replace("Z",""))
                        time_str = dt.strftime("%I:%M %p")
                    except Exception:
                        time_str = start_info["dateTime"][11:16]
                else:
                    time_str = "All day"
                color_data = ev.get("colorId", "")
                cal_colors = {"1":"#ac725e","2":"#d06b64","3":"#f83a22","4":"#fa573c",
                              "5":"#ff7537","6":"#ffad46","7":"#42d692","8":"#16a765",
                              "9":"#7bd148","10":"#b3dc6c","11":"#fbe983"}
                dot_color = cal_colors.get(color_data, "#d4681e")
                location_html = ""
                if ev.get("location"):
                    location_html = f'<br><span style="font-size:.65rem;color:#9a8878">📍 {ev["location"][:60]}</span>'
                st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{dot_color};padding:.45rem 1rem;margin:.2rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:.85rem;color:#f0e6d3">{ev.get('summary','(No title)')}</span>
    <span style="font-size:.7rem;color:#9a8878;font-family:'Space Mono',monospace">{time_str}</span>
  </div>
  {location_html}
  {f'<div style="font-size:.65rem;color:#9a8878;margin-top:.15rem">{ev.get("description","")[:80]}</div>' if ev.get("description") else ""}
</div>""", unsafe_allow_html=True)

with tab_add:
    service2, _ = get_calendar_service() if CREDENTIALS_FILE.exists() else (None, None)
    if not service2:
        st.warning("Connect your calendar first (place credentials.json in dashboard folder and refresh).")
    else:
        with st.form("add_event"):
            ev_title = st.text_input("Event Title *")
            c1, c2 = st.columns(2)
            with c1:
                ev_date  = st.date_input("Date", value=datetime.date.today())
                ev_start = st.time_input("Start Time", value=datetime.time(9, 0))
            with c2:
                ev_end   = st.time_input("End Time", value=datetime.time(10, 0))
                ev_loc   = st.text_input("Location (optional)")
            ev_desc  = st.text_area("Description", height=80)
            if st.form_submit_button("Create Event"):
                if ev_title.strip():
                    try:
                        tz = "America/New_York"
                        start_dt = datetime.datetime.combine(ev_date, ev_start).isoformat()
                        end_dt   = datetime.datetime.combine(ev_date, ev_end).isoformat()
                        body = {
                            "summary": ev_title.strip(),
                            "location": ev_loc,
                            "description": ev_desc,
                            "start": {"dateTime": start_dt, "timeZone": tz},
                            "end":   {"dateTime": end_dt,   "timeZone": tz},
                        }
                        service2.events().insert(calendarId="primary", body=body).execute()
                        st.session_state.pop("cal_events", None)
                        st.success("Event created!"); st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Title required.")
