import streamlit as st, sys, datetime, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Investments · Jarvis", page_icon="📈", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
import plotly.graph_objects as go
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

def get_price(symbol):
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        data = t.fast_info
        return round(float(data.last_price), 2)
    except Exception:
        return None

page_header("📈", "Investment Tracker", "portfolio · watchlist · petrodollar thesis")

tab_port, tab_watch, tab_trans, tab_research, tab_manage = st.tabs([
    "💼 Portfolio", "👁 Watchlist", "📋 Transactions", "🔭 Research Notes", "⚙️ Manage"])

THESIS_COLORS = {
    "petrodollar":  "#c4a882",
    "ai-bubble":    "#8b4049",
    "fortress-america": "#d4681e",
    "domestic-energy": "#7a8c6e",
    "general":      "#9a8878",
}
THESIS_LABELS = {
    "petrodollar":  "Petrodollar Collapse",
    "ai-bubble":    "AI Bubble Pop",
    "fortress-america": "Fortress America",
    "domestic-energy": "Domestic Energy",
    "general":      "General",
}

# ══════════════════════ PORTFOLIO ═══════════════════════════════════════════
with tab_port:
    holdings = get_q("SELECT id,account,symbol,shares,avg_cost,notes FROM portfolio_holdings ORDER BY account,symbol")
    total_deposits = get1("SELECT COALESCE(SUM(amount),0) FROM cash_deposits")[0]

    if holdings:
        # Group by account
        accounts = {}
        for h in holdings:
            accounts.setdefault(h[1], []).append(h)

        grand_val = 0.0; grand_cost = 0.0
        price_cache = {}

        for account, holds in accounts.items():
            st.markdown(f'<div style="font-family:Playfair Display,serif;font-size:1.1rem;color:#c4a882;margin:1rem 0 .5rem">Account: {account.title()}</div>', unsafe_allow_html=True)
            acc_val = 0.0; acc_cost = 0.0
            rows_html = ""
            for h in holds:
                hid, acc, sym, shares, avg_cost, notes = h
                if sym not in price_cache:
                    price_cache[sym] = get_price(sym)
                price = price_cache[sym]
                shares = shares or 0; avg_cost = avg_cost or 0
                val  = (price * shares)    if price else None
                cost = avg_cost * shares
                if val is not None:
                    pnl  = val - cost
                    pct  = (pnl / cost * 100) if cost else 0
                    acc_val  += val;  grand_val  += val
                    acc_cost += cost; grand_cost += cost
                    pnl_color = "#7a8c6e" if pnl >= 0 else "#8b4049"
                    price_str = f"${price:.2f}"
                    val_str   = f"${val:,.0f}"
                    pct_str   = f"{pct:+.1f}%"
                else:
                    pnl_color="#9a8878"; price_str="—"; val_str="—"; pct_str="—"

                rows_html += f"""
<div style="display:grid;grid-template-columns:80px 70px 70px 90px 90px 1fr;
gap:.3rem;align-items:center;padding:.3rem .5rem;background:#23201c;border-radius:3px;
margin:.1rem 0;font-size:.78rem;font-family:'Space Mono',monospace">
  <span style="color:#f0e6d3;font-weight:700">{sym}</span>
  <span style="color:#9a8878">{shares:.2f} sh</span>
  <span style="color:#9a8878">${avg_cost:.2f}</span>
  <span style="color:#c4a882">{price_str}</span>
  <span style="color:{pnl_color}">{pct_str}</span>
  <span style="color:#9a8878;font-size:.7rem">{notes or ''}</span>
</div>"""
            st.markdown(f"""
<div style="font-size:.62rem;color:#9a8878;display:grid;grid-template-columns:80px 70px 70px 90px 90px 1fr;gap:.3rem;padding:.2rem .5rem;text-transform:uppercase;letter-spacing:1px">
  <span>Symbol</span><span>Shares</span><span>Avg Cost</span><span>Price</span><span>Return</span><span>Notes</span>
</div>{rows_html}""", unsafe_allow_html=True)

            if acc_val:
                acc_gain = acc_val - acc_cost
                acc_pct  = (acc_gain / acc_cost * 100) if acc_cost else 0
                st.markdown(f'<div style="text-align:right;font-size:.78rem;color:#9a8878;margin-bottom:.5rem">Subtotal: <span style="color:#f0e6d3;font-family:Space Mono,monospace">${acc_val:,.0f}</span> &nbsp; <span style="color:{"#7a8c6e" if acc_gain>=0 else "#8b4049"}">{acc_pct:+.1f}%</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
        # Performance split: market gains vs deposits
        if grand_cost > 0:
            market_gain = grand_val - grand_cost
            pct_gain    = (market_gain / grand_cost * 100)
            col_s1,col_s2,col_s3,col_s4 = st.columns(4)
            col_s1.metric("Total Market Value",  f"${grand_val:,.0f}")
            col_s2.metric("Total Cost Basis",    f"${grand_cost:,.0f}")
            col_s3.metric("Market Gain/Loss",    f"${market_gain:+,.0f}", f"{pct_gain:+.2f}%",
                          delta_color="normal" if market_gain >= 0 else "inverse")
            col_s4.metric("Total Cash Deposited", f"${total_deposits:,.0f}",
                          help="External cash deposits — excluded from performance calculation")

            st.markdown("""<div class="vinyl-card vinyl-card-gold" style="font-size:.78rem;margin-top:.5rem">
<b>Performance Transparency:</b> The <span style="color:#c4a882">Market Gain/Loss</span> figure reflects
actual investment returns, <b>excluding</b> outside cash deposits. Cash deposits are tracked separately
to give you an honest picture of your portfolio's performance.
</div>""", unsafe_allow_html=True)
    else:
        st.info("No holdings added yet. Add them in the Manage tab.")

# ══════════════════════ WATCHLIST ════════════════════════════════════════════
with tab_watch:
    watchlist = get_q("SELECT id,symbol,target_price,alert_price,thesis,notes FROM watchlist ORDER BY thesis,symbol")

    if watchlist:
        # Header
        st.markdown("""
<div style="display:grid;grid-template-columns:80px 90px 90px 90px 140px 1fr;gap:.3rem;
padding:.25rem .5rem;font-size:.62rem;color:#9a8878;text-transform:uppercase;letter-spacing:1px">
  <span>Symbol</span><span>Price</span><span>Target</span><span>Alert</span><span>Thesis</span><span>Notes</span>
</div>""", unsafe_allow_html=True)

        for w in watchlist:
            wid, wsym, wtgt, walert, wthesis, wnotes = w
            price = get_price(wsym)
            tc    = THESIS_COLORS.get(wthesis, "#9a8878")
            price_str = f"${price:.2f}" if price else "—"
            tgt_str   = f"${wtgt:.2f}" if wtgt else "—"
            alert_str = f"${walert:.2f}" if walert else "—"
            at_alert  = price and walert and price <= walert
            at_target = price and wtgt and price >= wtgt
            row_bg    = "rgba(212,104,30,.08)" if at_alert else "rgba(122,140,110,.06)" if at_target else "#23201c"
            price_color = "#7a8c6e" if at_target else "#8b4049" if at_alert else "#f0e6d3"

            col_r, col_d = st.columns([8,1])
            with col_r:
                st.markdown(f"""
<div style="display:grid;grid-template-columns:80px 90px 90px 90px 140px 1fr;gap:.3rem;
align-items:center;padding:.3rem .5rem;background:{row_bg};border-radius:3px;
margin:.1rem 0;font-size:.78rem;font-family:Space Mono,monospace">
  <span style="color:#f0e6d3;font-weight:700">{wsym}</span>
  <span style="color:{price_color}">{price_str}</span>
  <span style="color:#7a8c6e">{tgt_str}</span>
  <span style="color:#8b4049">{alert_str}</span>
  <span style="color:{tc};font-size:.68rem">{THESIS_LABELS.get(wthesis,'—')}</span>
  <span style="color:#9a8878;font-size:.7rem">{wnotes or ''}</span>
</div>""", unsafe_allow_html=True)
            with col_d:
                if st.button("🗑", key=f"wdel_{wid}"):
                    run_q("DELETE FROM watchlist WHERE id=?", (wid,)); st.rerun()

    with st.expander("＋ Add to Watchlist"):
        with st.form("add_watch"):
            wc1,wc2,wc3 = st.columns(3)
            with wc1:
                w_sym   = st.text_input("Symbol *").upper()
                w_notes = st.text_input("Notes/Thesis summary")
            with wc2:
                w_tgt   = st.number_input("Target Price ($)", 0.0, 10000.0, 0.0, 1.0)
                w_alert = st.number_input("Alert Price ($)",  0.0, 10000.0, 0.0, 1.0)
            with wc3:
                w_thesis = st.selectbox("Thesis Tag",
                    ["fortress-america","petrodollar","ai-bubble","domestic-energy","general"])
            if st.form_submit_button("Add"):
                if w_sym.strip():
                    run_q("INSERT OR IGNORE INTO watchlist (symbol,target_price,alert_price,thesis,notes) VALUES (?,?,?,?,?)",
                          (w_sym.strip(), w_tgt if w_tgt else None, w_alert if w_alert else None, w_thesis, w_notes.strip()))
                    st.rerun()

# ══════════════════════ TRANSACTIONS ════════════════════════════════════════
with tab_trans:
    col_tx, col_dep = st.columns([1, 1])

    with col_tx:
        st.markdown("### Log Transaction")
        with st.form("add_tx"):
            tc1,tc2 = st.columns(2)
            with tc1:
                tx_date = st.date_input("Date", value=today)
                tx_acc  = st.text_input("Account", placeholder="individual / roth / brokerage")
                tx_sym  = st.text_input("Symbol").upper()
            with tc2:
                tx_type = st.selectbox("Type", ["buy","sell","dividend"])
                tx_sh   = st.number_input("Shares", 0.0, 100000.0, 1.0, 0.01)
                tx_price= st.number_input("Price ($)", 0.0, 100000.0, 100.0, 0.01)
            tx_notes= st.text_input("Notes")
            if st.form_submit_button("Log"):
                if tx_sym.strip() and tx_acc.strip():
                    run_q("INSERT INTO portfolio_transactions (date,account,symbol,transaction_type,shares,price,notes) VALUES (?,?,?,?,?,?,?)",
                          (str(tx_date), tx_acc.strip(), tx_sym.strip(), tx_type, tx_sh, tx_price, tx_notes))
                    st.success("Transaction logged!"); st.rerun()

    with col_dep:
        st.markdown("### Log Cash Deposit")
        st.markdown('<div style="font-size:.78rem;color:#9a8878;margin-bottom:.5rem">Track outside deposits separately from market performance.</div>', unsafe_allow_html=True)
        with st.form("add_deposit"):
            dc1,dc2 = st.columns(2)
            with dc1:
                dep_date = st.date_input("Date", value=today, key="dep_date")
                dep_acc  = st.text_input("Account", key="dep_acc")
            with dc2:
                dep_amt  = st.number_input("Amount ($)", 0.0, 1000000.0, 1000.0, 100.0)
                dep_notes= st.text_input("Notes", key="dep_notes", placeholder="e.g. Monthly contribution")
            if st.form_submit_button("Log Deposit"):
                if dep_acc.strip() and dep_amt > 0:
                    run_q("INSERT INTO cash_deposits (date,account,amount,notes) VALUES (?,?,?,?)",
                          (str(dep_date), dep_acc.strip(), dep_amt, dep_notes))
                    st.success(f"Logged ${dep_amt:,.0f} deposit!"); st.rerun()

    recent_tx = get_q("SELECT date,account,symbol,transaction_type,shares,price FROM portfolio_transactions ORDER BY date DESC LIMIT 20")
    st.markdown("### Recent Transactions")
    for tx in recent_tx:
        ttype_color = {"buy":"#7a8c6e","sell":"#8b4049","dividend":"#c4a882"}.get(tx[3],"#9a8878")
        total_val   = (tx[4] or 0) * (tx[5] or 0)
        st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:.25rem .7rem;
background:#23201c;border-radius:3px;margin:.1rem 0;font-size:.78rem;font-family:Space Mono,monospace">
  <span style="color:{ttype_color};text-transform:uppercase;width:60px">{tx[3]}</span>
  <span style="color:#f0e6d3;font-weight:700;width:60px">{tx[2]}</span>
  <span style="color:#9a8878">{tx[4]:.2f} sh @ ${tx[5]:.2f}</span>
  <span style="color:#c4a882">${total_val:,.0f}</span>
  <span style="color:#9a8878">{tx[0]} · {tx[1]}</span>
</div>""", unsafe_allow_html=True)

    recent_dep = get_q("SELECT date,account,amount,notes FROM cash_deposits ORDER BY date DESC LIMIT 10")
    if recent_dep:
        st.markdown("### Recent Deposits")
        for d in recent_dep:
            st.markdown(f"""
<div style="display:flex;justify-content:space-between;padding:.25rem .7rem;background:#23201c;
border-radius:3px;margin:.1rem 0;font-size:.78rem;font-family:Space Mono,monospace">
  <span style="color:#c4a882">DEPOSIT</span>
  <span style="color:#f0e6d3">${d[2]:,.0f}</span>
  <span style="color:#9a8878">{d[1]} · {d[0]}</span>
  <span style="color:#9a8878">{d[3] or ''}</span>
</div>""", unsafe_allow_html=True)

# ══════════════════════ RESEARCH NOTES ══════════════════════════════════════
with tab_research:
    st.markdown("### 🔭 Investment Research Notes")
    st.markdown('<div class="vinyl-card vinyl-card-gold" style="font-size:.8rem">Log your research, thesis notes, and market observations. Tag by investment thesis to build your knowledge base.</div>', unsafe_allow_html=True)

    thesis_filter = st.selectbox("Filter by thesis", ["all"] + list(THESIS_LABELS.keys()), key="rn_filter")
    where = "" if thesis_filter == "all" else f"WHERE thesis_tag='{thesis_filter}'"
    notes = get_q(f"SELECT id,date,title,content,thesis_tag FROM research_notes {where} ORDER BY date DESC, id DESC")

    for n in notes:
        nid,ndate,ntitle,ncontent,nthesis = n
        tc = THESIS_COLORS.get(nthesis,"#9a8878")
        tl = THESIS_LABELS.get(nthesis,"General")
        with st.expander(f"{ndate} — {ntitle or '(untitled)'}  [{tl}]"):
            st.markdown(f'<div style="color:{tc};font-size:.68rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:.3rem">{tl}</div>', unsafe_allow_html=True)
            st.markdown(ncontent or "")
            if st.button("🗑 Delete note", key=f"rndel_{nid}"):
                run_q("DELETE FROM research_notes WHERE id=?", (nid,)); st.rerun()

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    with st.form("add_research_note"):
        rn1,rn2 = st.columns(2)
        with rn1:
            rn_date   = st.date_input("Date", value=today)
            rn_title  = st.text_input("Title")
        with rn2:
            rn_thesis = st.selectbox("Thesis Tag", list(THESIS_LABELS.keys()))
            rn_tags   = st.text_input("Tags (comma-separated)")
        rn_content = st.text_area("Notes / Research", height=160,
            placeholder="e.g. Watched Jiang Xueqin latest — thesis developing around BRICS settlement in gold, de-dollarization accelerating. Key signal: Saudi Aramco accepting yuan for oil exports. Monitor: DXY, 10yr yield spread vs TIPS...")
        if st.form_submit_button("Save Note"):
            if rn_content.strip():
                run_q("INSERT INTO research_notes (date,title,content,tags,thesis_tag) VALUES (?,?,?,?,?)",
                      (str(rn_date), rn_title.strip(), rn_content.strip(), rn_tags.strip(), rn_thesis))
                st.rerun()

    # Quick-reference thesis framework
    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📌 Thesis Framework Reference")
    framework = {
        "🏰 Fortress America": "Domestic industrials, grid infrastructure, domestic energy. Insulated from foreign bond liquidation. Key names: HUBB, GEV, CF Industries, domestic refiners.",
        "🛢 Petrodollar Collapse": "Prof. Jiang Xueqin thesis: USD hegemony eroding via BRICS, yuan oil settlement. Monitor: DXY, gold, 10yr Treasuries, Saudi/Russian energy flows. PHYS/PSLV as sovereign hedges.",
        "⚡ Domestic Energy": "US energy independence plays insulated from Hormuz risk. Refiners, nat gas producers, grid infrastructure. Avoid pure global oil exposure.",
        "🫧 AI Bubble Pop": "Valuation risk in hyperscalers and semiconductor supply chain. Avoid late-cycle AI capex beneficiaries. Watch for NVDA earnings guidance deterioration.",
    }
    for title_f, desc in framework.items():
        st.markdown(f"""
<div class="vinyl-card" style="margin:.3rem 0;padding:.5rem 1rem">
  <div style="font-size:.85rem;color:#c4a882;margin-bottom:.2rem">{title_f}</div>
  <div style="font-size:.78rem;color:#9a8878">{desc}</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════ MANAGE ═══════════════════════════════════════════════
with tab_manage:
    st.markdown("### ⚙️ Manage Holdings")
    with st.form("add_holding"):
        hc1,hc2,hc3 = st.columns(3)
        with hc1:
            h_acc  = st.text_input("Account *", placeholder="individual / roth")
            h_sym  = st.text_input("Symbol *").upper()
        with hc2:
            h_sh   = st.number_input("Shares", 0.0, 1000000.0, 1.0, 0.01)
            h_cost = st.number_input("Avg Cost ($)", 0.0, 100000.0, 100.0, 0.01)
        with hc3:
            h_notes= st.text_area("Notes", height=68)
        if st.form_submit_button("Add/Update Holding"):
            if h_sym.strip() and h_acc.strip():
                existing = get1("SELECT id FROM portfolio_holdings WHERE account=? AND symbol=?",
                                (h_acc.strip(), h_sym.strip()))
                if existing:
                    run_q("UPDATE portfolio_holdings SET shares=?,avg_cost=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                          (h_sh, h_cost, h_notes.strip(), existing[0]))
                else:
                    run_q("INSERT INTO portfolio_holdings (account,symbol,shares,avg_cost,notes) VALUES (?,?,?,?,?)",
                          (h_acc.strip(), h_sym.strip(), h_sh, h_cost, h_notes.strip()))
                st.success("Updated!"); st.rerun()

    all_holdings = get_q("SELECT id,account,symbol,shares,avg_cost FROM portfolio_holdings ORDER BY account,symbol")
    for h in all_holdings:
        col_a, col_b = st.columns([5,1])
        with col_a:
            st.markdown(f'<div style="font-size:.8rem;padding:.25rem .5rem;background:#23201c;border-radius:3px;margin:.1rem 0;font-family:Space Mono,monospace"><span style="color:#c4a882">{h[1]}</span> · <span style="color:#f0e6d3">{h[2]}</span> · {h[3]:.2f} shares @ ${h[4]:.2f}</div>', unsafe_allow_html=True)
        with col_b:
            if st.button("🗑", key=f"hdel_{h[0]}"):
                run_q("DELETE FROM portfolio_holdings WHERE id=?", (h[0],)); st.rerun()

conn.close()
