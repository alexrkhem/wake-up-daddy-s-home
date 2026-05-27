import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """You are Jarvis — a calm, sharp, direct AI assistant embedded in a personal dashboard.
Your user tracks: todos, sleep, fitness (weightlifting, steps, height training), nutrition (Cronometer CSV),
music (guitar & euphonium), academics (Linear Algebra, Statics, Chemistry), investments (Fortress America thesis,
petrodollar collapse research, domestic energy plays), design projects, and a personal journal/win-streak log.

Keep responses concise. When teaching academics: clear step-by-step math. On investments: analytical commentary
only, grounded in Fortress America / petrodollar thesis. No financial advice.
Tone: thoughtful, efficient — like a brilliant record-shop clerk."""

def render_jarvis_sidebar(rag_context: str = ""):
    with st.sidebar:
        st.markdown("""
<div style="text-align:center;padding:1rem 0 0.5rem">
  <div style="font-family:'Playfair Display',serif;font-size:1.4rem;color:#c4a882">J A R V I S</div>
  <div style="font-size:0.62rem;color:#9a8878;letter-spacing:2px;text-transform:uppercase">AI Assistant</div>
  <div style="height:1px;background:linear-gradient(to right,transparent,#c4a882,transparent);margin:.7rem 0"></div>
</div>""", unsafe_allow_html=True)

        if not ANTHROPIC_API_KEY:
            st.warning("Set ANTHROPIC_API_KEY in .env to activate Jarvis.")
            _nav_links()
            return

        if "jarvis_msgs" not in st.session_state:
            st.session_state.jarvis_msgs = []

        for msg in st.session_state.jarvis_msgs[-4:]:
            color = "#c4a882" if msg["role"] == "assistant" else "#d4681e"
            ico   = "◈" if msg["role"] == "assistant" else "◉"
            text  = msg['content'][:220] + ("…" if len(msg['content']) > 220 else "")
            st.markdown(f"""<div style="background:#23201c;border-left:2px solid {color};
padding:.45rem .7rem;margin:.3rem 0;border-radius:0 3px 3px 0;font-size:.77rem">
<span style="color:{color}">{ico} </span><span style="color:#f0e6d3">{text}</span></div>""",
                        unsafe_allow_html=True)

        prompt = st.chat_input("Ask Jarvis…", key="jarvis_input")
        if prompt:
            st.session_state.jarvis_msgs.append({"role": "user", "content": prompt})
            with st.spinner("thinking…"):
                try:
                    import anthropic as _ant
                    client = _ant.Anthropic(api_key=ANTHROPIC_API_KEY)
                    sys_p  = SYSTEM_PROMPT + (f"\n\nTextbook context:\n{rag_context}" if rag_context else "")
                    msgs   = [{"role": m["role"], "content": m["content"]}
                              for m in st.session_state.jarvis_msgs[-10:]]
                    resp   = client.messages.create(model="claude-sonnet-4-20250514",
                                                    max_tokens=900, system=sys_p, messages=msgs)
                    st.session_state.jarvis_msgs.append({"role": "assistant",
                                                         "content": resp.content[0].text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Jarvis: {e}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clear", key="jclr", use_container_width=True):
                st.session_state.jarvis_msgs = []
                st.rerun()
        with c2:
            n = len(st.session_state.get("jarvis_msgs", []))
            st.markdown(f'<div style="font-size:.65rem;color:#9a8878;text-align:center;padding-top:.5rem">{n} msgs</div>',
                        unsafe_allow_html=True)
        st.markdown('<hr style="border:none;border-top:1px solid #3d3028;margin:1rem 0">', unsafe_allow_html=True)
        _nav_links()

def _nav_links():
    pages = [
        ("📋", "Todo"),       ("📅", "Calendar"),
        ("😴", "Sleep"),      ("💪", "Fitness"),
        ("🍎", "Nutrition"),  ("🎵", "Music"),
        ("📚", "Academics"),  ("📈", "Investments"),
        ("🎨", "Design"),     ("📓", "Journal"),
    ]
    for ico, name in pages:
        st.markdown(f'<div style="font-size:.75rem;color:#9a8878;padding:.15rem 0">{ico} {name}</div>',
                    unsafe_allow_html=True)
