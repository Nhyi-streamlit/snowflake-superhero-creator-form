import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Snowflake Community Voices — Program Dashboard",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  body, .main, .block-container, p, h1, h2, h3, li {
    font-family: 'Inter', sans-serif !important;
  }
  [data-testid="collapsedControl"] { display: none; }
  section[data-testid="stSidebar"]  { display: none; }

  .hero {
    background: #29B5E8;
    padding: 36px 48px;
    border-radius: 14px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 20px;
  }
  .hero h1 { color: #fff; font-size: 1.9rem; font-weight: 800; margin: 0 0 6px; }
  .hero p  { color: rgba(255,255,255,0.88); margin: 0; font-size: 0.95rem; }

  .stat-card {
    background: #F5F5F5;
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
  }
  .stat-card .number { font-size: 2.4rem; font-weight: 800; color: #29B5E8; line-height: 1; }
  .stat-card .label  { font-size: 0.78rem; color: #5B5B5B; margin-top: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }

  .section-header {
    font-size: 1.0rem; font-weight: 700; color: #0E2346;
    border-left: 4px solid #29B5E8;
    padding-left: 10px;
    margin: 28px 0 14px;
  }

  .asset-card {
    background: #fff;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
  }
  .asset-card a { color: #29B5E8; font-weight: 600; text-decoration: none; }
  .asset-card .desc { font-size: 0.82rem; color: #718096; margin-top: 4px; }

  .badge-accepted  { background: #C6F6D5; color: #22543D; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
  .badge-declined  { background: #FED7D7; color: #742A2A; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
  .badge-awaiting  { background: #FEFCBF; color: #744210; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
  .badge-unknown   { background: #EDF2F7; color: #4A5568; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Sheets data loader ─────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_sheet(sheet_name, range_suffix="!A1:Z200"):
    """Load data from Google Sheets via REST API."""
    refresh_token = client_id = client_secret = spreadsheet_id = ""
    try:
        refresh_token  = st.secrets.get("GOOGLE_REFRESH_TOKEN", "")
        client_id      = st.secrets.get("GOOGLE_CLIENT_ID", "")
        client_secret  = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
        spreadsheet_id = st.secrets.get("GOOGLE_SPREADSHEET_ID", "")
    except Exception:
        refresh_token  = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
        client_id      = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret  = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "")

    if not all([refresh_token, client_id, client_secret, spreadsheet_id]):
        return [], []

    tok = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token"
    }, timeout=10).json().get("access_token", "")

    if not tok:
        return [], []

    range_name = f"{sheet_name}{range_suffix}"
    resp = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{requests.utils.quote(range_name)}",
        headers={"Authorization": f"Bearer {tok}"}, timeout=15
    )
    values = resp.json().get("values", [])
    if not values:
        return [], []
    headers = values[0]
    rows = [dict(zip(headers, r + [""] * (len(headers) - len(r)))) for r in values[1:] if any(c.strip() for c in r)]
    return headers, rows


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <img src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg"
       height="40" style="filter:brightness(0) invert(1); flex-shrink:0;">
  <div>
    <h1>Snowflake Community Voices — Program Dashboard</h1>
    <p>Live overview of participants, submissions, assets, and launch markets · Updated in real time</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────────
_, project_rows     = load_sheet("Overall Project Sheet")
_, submission_rows  = load_sheet("Sheet1")
_, interest_rows    = load_sheet("Interested Speakers")
_, internal_rows    = load_sheet("Internal Submissions")
_, budget_rows      = load_sheet("Budget Breakdown")

# ── Credentials check ─────────────────────────────────────────────────────────
_has_creds = False
try:
    _has_creds = all([
        st.secrets.get("GOOGLE_REFRESH_TOKEN", ""),
        st.secrets.get("GOOGLE_CLIENT_ID", ""),
        st.secrets.get("GOOGLE_CLIENT_SECRET", ""),
        st.secrets.get("GOOGLE_SPREADSHEET_ID", ""),
    ])
except Exception:
    _has_creds = False

if not _has_creds:
    try:
        missing = [k for k in ["GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET","GOOGLE_SPREADSHEET_ID"]
                   if not st.secrets.get(k, "")]
    except Exception:
        missing = ["ALL (no secrets file found)"]
    st.error(
        f"**Missing secrets: {', '.join(missing)}**\n\n"
        "Make sure you saved these to **this dashboard app** (not the form app) on Streamlit Cloud:\n\n"
        "1. Go to [share.streamlit.io](https://share.streamlit.io)\n"
        "2. Find the app whose URL contains `dashboard` → **⋮ → Settings → Secrets**\n"
        "3. Paste your GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and "
        "GOOGLE_SPREADSHEET_ID values, then click **Save** and wait ~15 seconds for reboot."
    )


# ── Top-level stats ────────────────────────────────────────────────────────────
accepted  = sum(1 for r in project_rows if "accepted" in r.get("RSVP status", "").lower())
declined  = sum(1 for r in project_rows if "declined" in r.get("RSVP status", "").lower())
awaiting  = sum(1 for r in project_rows if "awaiting" in r.get("RSVP status", "").lower())
countries = len({r.get("Country ", r.get("Country", "")).strip() for r in project_rows if r.get("Country ", r.get("Country", "")).strip()})

c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, number, label in [
    (c1, len(project_rows),            "TOTAL PARTICIPANTS"),
    (c2, accepted,                     "ACCEPTED"),
    (c3, awaiting,                     "AWAITING RESPONSE"),
    (c4, len(interest_rows),           "INTERESTED SPEAKERS"),
    (c5, len(submission_rows),         "FORM SUBMISSIONS"),
    (c6, countries,                    "COUNTRIES REACHED"),
]:
    col.markdown(f"""
<div class="stat-card">
  <div class="number">{number}</div>
  <div class="label">{label}</div>
</div>""", unsafe_allow_html=True)

st.markdown("")

# ── Refresh button ────────────────────────────────────────────────────────────
refresh_col, _ = st.columns([1, 4])
with refresh_col:
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ── Accepted + Submissions side by side ───────────────────────────────────────
accepted_rows = [r for r in project_rows if "accepted" in r.get("RSVP status", "").lower()]

left_col, right_col = st.columns(2)

# Left: Accepted Participants from Overall Project Sheet
with left_col:
    st.markdown(f'<div class="section-header">✅ Accepted Participants ({len(accepted_rows)})</div>', unsafe_allow_html=True)
    if accepted_rows:
        for r in accepted_rows:
            name    = r.get("Name", "").strip()
            country = r.get("Country ", r.get("Country", "")).strip()
            city    = r.get("City", "").strip()
            email   = r.get("Email", "").strip()
            notes   = r.get("Notes", "").strip()
            loc     = ", ".join(x for x in [city, country] if x)
            st.markdown(f"""
<div style="background:#F0FFF4; border:1px solid #C6F6D5; border-radius:10px; padding:14px 16px; margin-bottom:8px;">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div style="font-weight:700; color:#0E2346; font-size:0.93rem;">{name}</div>
    <span class="badge-accepted">Accepted</span>
  </div>
  <div style="font-size:0.82rem; color:#4A5568; margin-top:3px;">📍 {loc}</div>
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px;">✉️ {email}</div>' if email else ''}
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:3px; font-style:italic;">{notes}</div>' if notes else ''}
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#718096; font-size:0.9rem; padding:12px 0;">No accepted participants yet — update the Overall Project Sheet to add them.</div>', unsafe_allow_html=True)

    # All participants expander — clean table
    with st.expander(f"All participants — {len(project_rows)} total", expanded=False):
        if project_rows:
            df = pd.DataFrame([{
                "Name":    r.get("Name", "").strip(),
                "City":    r.get("City", "").strip(),
                "Country": r.get("Country ", r.get("Country", "")).strip(),
                "Status":  r.get("RSVP status", "").strip() or "—",
                "Notes":   r.get("Notes", "").strip(),
            } for r in project_rows])
            st.dataframe(df, use_container_width=True, hide_index=True)

# Right: Form Submissions from Sheet1
with right_col:
    st.markdown(f'<div class="section-header">📋 Form Submissions ({len(submission_rows)})</div>', unsafe_allow_html=True)
    if submission_rows:
        for r in submission_rows:
            name    = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
            email   = r.get("Email", "").strip()
            event   = r.get("Event Name", "").strip()
            country = r.get("Country", "").strip()
            city    = r.get("City", "").strip()
            talk    = r.get("Talk Title", "").strip()
            sub_at  = r.get("Submitted At", "")[:10] if r.get("Submitted At") else ""
            loc     = ", ".join(x for x in [city, country] if x)
            st.markdown(f"""
<div style="background:#FFFAF0; border:1px solid #FEEBC8; border-radius:10px; padding:14px 16px; margin-bottom:8px;">
  <div style="font-weight:700; color:#0E2346; font-size:0.93rem;">{name or 'Anonymous'}</div>
  <div style="font-size:0.82rem; color:#4A5568; margin-top:3px;">📍 {loc}</div>
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px;">✉️ {email}</div>' if email else ''}
  {f'<div style="font-size:0.79rem; color:#0E2346; margin-top:3px; font-weight:600;">🎤 {event}</div>' if event else ''}
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px; font-style:italic;">{talk}</div>' if talk else ''}
  {f'<div style="font-size:0.77rem; color:#A0AEC0; margin-top:5px;">Submitted {sub_at}</div>' if sub_at else ''}
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#718096; font-size:0.9rem; padding:12px 0;">No form submissions yet — share the form to get started.</div>', unsafe_allow_html=True)

# ── Interested Speakers ─────────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">🙋 Interested Speakers ({len(interest_rows)})</div>', unsafe_allow_html=True)

if interest_rows:
    cols_per_row = 3
    for i in range(0, len(interest_rows), cols_per_row):
        chunk = interest_rows[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, r in zip(cols, chunk):
            name      = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
            country   = r.get("Country", "").strip()
            city      = r.get("City", "").strip()
            identity  = r.get("Community Identity", "").strip()
            topics    = r.get("Topics of Interest", "").strip()
            evt_types = r.get("Preferred Event Types", "").strip()
            sub_at    = r.get("Submitted At", "")[:10] if r.get("Submitted At") else ""
            loc       = ", ".join(x for x in [city, country] if x)
            col.markdown(f"""
<div style="background:#EBF8FF; border:1px solid #BEE3F8; border-radius:10px; padding:14px 16px; margin-bottom:8px;">
  <div style="font-weight:700; color:#0E2346; font-size:0.93rem; margin-bottom:3px;">{name or 'Anonymous'}</div>
  {f'<div style="font-size:0.82rem; color:#4A5568;">📍 {loc}</div>' if loc else ''}
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px;">👤 {identity}</div>' if identity else ''}
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px;">🎯 {topics[:80] + "…" if len(topics) > 80 else topics}</div>' if topics else ''}
  {f'<div style="font-size:0.79rem; color:#718096; margin-top:2px;">🗓 {evt_types}</div>' if evt_types else ''}
  {f'<div style="font-size:0.77rem; color:#A0AEC0; margin-top:5px;">{sub_at}</div>' if sub_at else ''}
</div>""", unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#718096; font-size:0.9rem; padding:12px 0;">No interest registrations yet.</div>', unsafe_allow_html=True)


# ── Budget ─────────────────────────────────────────────────────────────────────
if budget_rows:
    st.markdown('<div class="section-header">Partner Budget</div>', unsafe_allow_html=True)
    cols = st.columns(max(len(budget_rows), 1))
    for i, r in enumerate(budget_rows):
        partner = r.get("Partner", "").strip()
        amount  = r.get("Amount", "").strip()
        cities  = r.get("Cities", "").strip()
        if partner:
            cols[i % len(cols)].markdown(f"""
<div class="stat-card">
  <div style="font-size:1.1rem; font-weight:700; color:#0E2346; margin-bottom:4px;">{partner}</div>
  <div class="number" style="font-size:1.8rem;">{amount or "TBD"}</div>
  <div class="label">{cities + " cities" if cities else "partner"}</div>
</div>""", unsafe_allow_html=True)


# ── Launch markets ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Launch Markets — 14 Countries</div>', unsafe_allow_html=True)
markets = {
    "🌏 Asia Pacific":  ["Australia", "India", "Japan", "New Zealand", "South Korea"],
    "🌍 Europe":         ["Croatia", "Czech Republic", "Germany", "Italy", "Netherlands", "United Kingdom"],
    "🌎 Americas":       ["Brazil", "Canada", "United States"],
}
m1, m2, m3 = st.columns(3)
for col, (region, countries_list) in zip([m1, m2, m3], markets.items()):
    # Highlight countries that have participants
    participant_countries = {r.get("Country ", r.get("Country", "")).strip().lower() for r in project_rows}
    items = ""
    for c in countries_list:
        active = c.lower() in participant_countries
        dot = "🟢" if active else "⚪"
        items += f"<div style='padding:4px 0; font-size:0.88rem; color:#0E2346;'>{dot} {c}</div>"
    col.markdown(f"""
<div style="background:#F5F5F5; border-radius:10px; padding:16px 20px;">
  <div style="font-weight:700; color:#0E2346; margin-bottom:10px; font-size:0.95rem;">{region}</div>
  {items}
</div>""", unsafe_allow_html=True)


# ── Program assets ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Program Assets Built</div>', unsafe_allow_html=True)

assets = [
    ("🌐 Public Intake Form",
     "https://app-superhero-creator-form-5rkbvp9kjmrkjjkqfbslqj.streamlit.app",
     "Live Streamlit form for Data Superheroes & Streamlit Creators to apply for event support"),
    ("📊 Submissions Google Sheet",
     "https://docs.google.com/spreadsheets/d/1zQlOQYBqyVn9pAFjNQCM0LZleq1VktUmqFbuRq3Je8c/edit",
     "Tracks all form submissions, participant tracker, and budget breakdown"),
    ("📑 Community Guide (Public)",
     "https://docs.google.com/document/d/1yVZ0yjU39yrFI_4agcFlsrkVBdXALHbN1WcjDdOKWqk/edit",
     "Shareable guide explaining the program, eligibility, and how to apply"),
    ("🔒 Internal Operations Guide",
     "https://docs.google.com/document/d/1qyJ3Z7Q6oWddCXlBLM8zxPjBVmdarHpFAgU1ZCRDYzU/edit",
     "Snowflake-internal guide: scoring rubric, approval authority, budget, email templates"),
    ("📊 Snowflake Community Voices Slides",
     "https://docs.google.com/presentation/d/11Zp_FgI7RzLt4DXJfVIkvysOWiGYxJC4phz2YTsPxtI/edit",
     "6-slide Snowflake-branded presentation deck"),
    ("📊 Streamlit Community Voices Slides",
     "https://docs.google.com/presentation/d/1iA6lO_7vMGva2iFgCraw6I93QF8M0G5Kto59gO2J0do/edit",
     "6-slide Streamlit-branded presentation deck with white & red design"),
    ("💻 GitHub Code Repository",
     "https://github.com/Nhyi-streamlit/snowflake-superhero-creator-form",
     "Source code for the public form, internal form, and this dashboard"),
]

a1, a2 = st.columns(2)
for i, (title, url, desc) in enumerate(assets):
    col = a1 if i % 2 == 0 else a2
    col.markdown(f"""
<div class="asset-card">
  <a href="{url}" target="_blank">{title}</a>
  <div class="desc">{desc}</div>
</div>""", unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:#718096; font-size:0.8rem;'>"
    f"Snowflake Community Voices Program · Dashboard · Last refreshed: {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}"
    f"</div>",
    unsafe_allow_html=True
)
