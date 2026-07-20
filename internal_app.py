import os
import uuid
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Event Support — Snowflake Employees",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  html, body, [class*="st-"], .stTextInput input, .stSelectbox, .stMultiSelect,
  .stTextArea textarea, .stNumberInput input, .stRadio label, .stSlider,
  button, label, p, h1, h2, h3, span, div {
    font-family: 'Inter', sans-serif !important;
  }

  [data-testid="collapsedControl"] { display: none; }
  section[data-testid="stSidebar"] { display: none; }

  .page-hero {
    background: #29B5E8;
    padding: 48px 56px;
    border-radius: 16px;
    margin-bottom: 40px;
  }
  .page-hero .eyebrow {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: #fff;
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 16px;
  }
  .page-hero h1 { color: #FFFFFF; font-size: 2.1rem; font-weight: 800; line-height: 1.2; margin-bottom: 10px; }
  .page-hero p  { color: rgba(255,255,255,0.88); font-size: 1rem; max-width: 640px; margin: 0; }

  .step-label {
    display: inline-block;
    background: #EBF8FF;
    color: #29B5E8;
    border: 1px solid #BEE3F8;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .section-title { font-size: 1.2rem; font-weight: 700; color: #0E2346; margin: 4px 0 2px; }
  .section-hint  { font-size: 0.88rem; color: #64748B; margin-bottom: 18px; }

  .success-box {
    background: linear-gradient(135deg, #0E2346, #1B3A6B);
    padding: 56px;
    border-radius: 16px;
    text-align: center;
    color: #fff;
    margin: 40px auto;
    max-width: 600px;
  }
  .success-box h2 { font-size: 1.8rem; font-weight: 800; margin-bottom: 12px; }
  .success-box p  { color: #A8D8F0; font-size: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Sheets helper ──────────────────────────────────────────────────────────────
def _get_sheets_access_token(refresh_token: str, client_id: str, client_secret: str) -> str:
    import requests
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def save_submission(data: dict) -> bool:
    """Append row to the 'Internal Submissions' tab in Google Sheets."""
    import requests

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
        st.error("Submission backend not configured.")
        return False

    try:
        access_token = _get_sheets_access_token(refresh_token, client_id, client_secret)
        row = [
            data.get("submission_id", ""),
            data.get("submitted_at", ""),
            data.get("first_name", ""),
            data.get("last_name", ""),
            data.get("email", ""),
            data.get("team", ""),
            data.get("country", ""),
            data.get("city", ""),
            data.get("event_name", ""),
            data.get("event_link", ""),
            data.get("talk_title", ""),
            data.get("session_type", ""),
            ", ".join(data.get("snowflake_topics", [])),
            data.get("support_rank_1", ""),
            data.get("support_rank_2", ""),
            data.get("support_rank_3", ""),
            str(data.get("estimated_cost", 0)),
            data.get("traveling_from", ""),
            data.get("additional_notes", ""),
        ]
        resp = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            f"/values/Internal%20Submissions!A:T:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [row]},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        st.error(f"Sheets write failed ({resp.status_code}): {resp.text[:200]}")
        return False
    except Exception as e:
        st.error(f"Submission error: {e}")
        return False


# ── Session state ──────────────────────────────────────────────────────────────
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "num_events" not in st.session_state:
    st.session_state.num_events = 1

# ── Success screen ─────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown("""
<div class="success-box">
  <div style="font-size:2.5rem; margin-bottom:16px;">❄️</div>
  <h2>You're on our radar!</h2>
  <p>Thanks for submitting — the Snowflake Community team will be in touch
  to discuss how we can support you at this event.</p>
</div>
""", unsafe_allow_html=True)
    if st.button("Submit another event"):
        st.session_state.submitted = False
        st.session_state.num_events = 1
        st.rerun()
    st.stop()


# ── Constants ──────────────────────────────────────────────────────────────────
COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Argentina","Armenia","Australia",
    "Austria","Azerbaijan","Bahrain","Bangladesh","Belarus","Belgium","Bolivia","Bosnia",
    "Brazil","Bulgaria","Cambodia","Canada","Chile","China","Colombia","Costa Rica","Croatia",
    "Czech Republic","Denmark","Ecuador","Egypt","Estonia","Ethiopia","Finland","France",
    "Georgia","Germany","Ghana","Greece","Guatemala","Honduras","Hungary","India","Indonesia",
    "Iran","Iraq","Ireland","Israel","Italy","Japan","Jordan","Kazakhstan","Kenya","Kosovo",
    "Latvia","Lebanon","Lithuania","Luxembourg","Malaysia","Mexico","Moldova","Morocco",
    "Netherlands","New Zealand","Nigeria","Norway","Pakistan","Palestine","Panama","Peru",
    "Philippines","Poland","Portugal","Romania","Russia","Saudi Arabia","Senegal","Serbia",
    "Singapore","Slovakia","Slovenia","South Africa","South Korea","Spain","Sri Lanka","Sweden",
    "Switzerland","Taiwan","Thailand","Turkey","Ukraine","United Arab Emirates",
    "United Kingdom","United States","Uruguay","Uzbekistan","Venezuela","Vietnam","Zimbabwe",
    "Other",
]

SNOWFLAKE_TEAMS = [
    "— select —",
    "Developer Relations",
    "Product Marketing",
    "Engineering",
    "Product Management",
    "Sales / Solutions Engineering",
    "Marketing",
    "Data Science / AI",
    "Design",
    "Legal / Compliance",
    "Operations",
    "Executive / Leadership",
    "Other",
]

SNOWFLAKE_TOPICS = [
    "Snowflake Data Cloud",
    "Cortex AI / LLM functions",
    "Cortex Analyst / Semantic Views",
    "Cortex Code (CoCo) — AI-powered IDE",
    "CoCo Skills & Agents",
    "CoCo + Data Engineering",
    "CoCo + Streamlit",
    "Snowpark (Python / Java / Scala)",
    "Streamlit in Snowflake",
    "Native Apps / App Framework",
    "Iceberg / Open Table Formats",
    "Data Sharing / Marketplace",
    "Dynamic Tables / Pipelines",
    "Data Governance / Horizon",
    "Snowpipe / Streaming Ingestion",
    "Snowflake ML / Feature Store",
    "Performance & Cost Optimization",
    "AI Agents on Snowflake",
    "Open Source + Snowflake",
    "Other",
]

INTERNAL_SUPPORT_OPTIONS = [
    "— none —",
    "Travel budget approval",
    "Hotel / accommodation",
    "Event registration / ticket",
    "Speaking coaching",
    "Talk / slide deck review",
    "Snowflake branding assets",
    "Social amplification",
    "Snowflake Community team co-presentation",
    "Snowflake swag / materials",
    "Event logistics support",
]

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div style="display:flex; align-items:center; gap:14px; margin-bottom:18px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg"
         alt="Snowflake" height="36"
         style="filter:brightness(0) invert(1); flex-shrink:0;">
    <div class="eyebrow" style="margin-bottom:0;">Snowflake Internal · Event Support</div>
  </div>
  <h1>Speaking at an Event?<br>Let Us Help.</h1>
  <p>Snowflake employees heading to a conference, meetup, or event — fill out this form
  so the Snowflake Community team can assess how to best support you.</p>
</div>
""", unsafe_allow_html=True)


# ── Form ───────────────────────────────────────────────────────────────────────
with st.form("internal_event_form", clear_on_submit=False):

    # ── Section 1: About You ──────────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 1 of 3</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">About You</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Your basic details so we can follow up.</p>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        first_name = st.text_input("First name", placeholder="Aba")
        country    = st.selectbox("Country", ["— select —"] + COUNTRIES)
        email      = st.text_input("Email address", placeholder="you@snowflake.com")
    with a2:
        last_name  = st.text_input("Last name", placeholder="Micah")
        city       = st.text_input("City", placeholder="San Francisco")
        team       = st.selectbox("Team / Department", SNOWFLAKE_TEAMS)

    # ── Email validation notice (non-blocking) ────────────────────────────────
    if email and not email.strip().endswith("@snowflake.com"):
        st.warning("This form is for Snowflake employees. Please use your @snowflake.com email.")

    st.divider()

    # ── Section 2: The Event ──────────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 2 of 3</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">The Event</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us about the conference, event, or meetup you\'re planning to attend or speak at.</p>', unsafe_allow_html=True)

    event_entries = []
    for i in range(st.session_state.num_events):
        label = f"Event {i + 1}" if st.session_state.num_events > 1 else "Event"
        ec1, ec2 = st.columns(2)
        with ec1:
            ename = st.text_input(f"{label} name", placeholder="PyCon US 2025, local data meetup, etc.", key=f"event_name_{i}")
        with ec2:
            elink = st.text_input(f"{label} link", placeholder="https://us.pycon.org", key=f"event_link_{i}")
        event_entries.append((ename, elink))

    add_event_btn = st.form_submit_button("＋ Add another event", type="secondary")

    event_name = " | ".join(e[0] for e in event_entries if e[0].strip())
    event_link = " | ".join(e[1] for e in event_entries if e[1].strip())

    st.divider()

    # ── Section 3: Talk & Support ─────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 3 of 3</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Talk & Support</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us what you\'re presenting and what kind of support would help most.</p>', unsafe_allow_html=True)

    ts1, ts2 = st.columns(2)
    with ts1:
        talk_title = st.text_input(
            "Talk / session title",
            placeholder="Building Production AI Agents on Snowflake",
            help="Leave blank if not finalised yet.",
        )
        session_type = st.selectbox(
            "Session type",
            ["— select —", "Keynote", "Talk (30–45 min)", "Lightning Talk (5–15 min)",
             "Workshop / Tutorial", "Panel", "Poster / Demo", "Not yet confirmed", "Other"],
        )
    with ts2:
        snowflake_topics_selected = st.multiselect(
            "Snowflake topics you'll cover",
            SNOWFLAKE_TOPICS,
        )

    st.markdown("**What support are you looking for?** Rank your top 3.")
    rk1, rk2, rk3 = st.columns(3)
    with rk1:
        support_rank_1 = st.selectbox("1st priority", INTERNAL_SUPPORT_OPTIONS, index=0)
    with rk2:
        support_rank_2 = st.selectbox("2nd priority", INTERNAL_SUPPORT_OPTIONS, index=0)
    with rk3:
        support_rank_3 = st.selectbox("3rd priority", INTERNAL_SUPPORT_OPTIONS, index=0)

    sup1, sup2 = st.columns(2)
    with sup1:
        estimated_cost = st.number_input(
            "Estimated travel cost (USD)",
            min_value=0, max_value=25000, step=50, value=500,
            help="Rough estimate — flights + hotel if applicable.",
        )
    with sup2:
        traveling_from = st.text_input("Traveling from (city, country)", placeholder="San Francisco, USA")

    additional_notes = st.text_area(
        "Anything else you'd like us to know?",
        placeholder="Context, timing constraints, co-presenters, manager approval status, etc.",
        height=100,
    )

    st.markdown("")

    with st.container(border=True):
        st.caption(
            "By submitting this form you agree to be contacted by the Snowflake Community team "
            "regarding event support. Your information will only be used to evaluate and manage this program."
        )
        submitted = st.form_submit_button(
            "Submit — Let us know you're going →",
            type="primary",
            use_container_width=True,
        )

    # ── Handlers ──────────────────────────────────────────────────────────────
    if add_event_btn:
        st.session_state.num_events += 1
        st.rerun()

    if submitted:
        if email.strip() and not email.strip().endswith("@snowflake.com"):
            st.error("Please use your @snowflake.com email address to submit this form.")
        else:
            payload = {
                "submission_id": str(uuid.uuid4()),
                "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "team": team if team != "— select —" else "",
                "country": country if country != "— select —" else "",
                "city": city.strip(),
                "event_name": event_name,
                "event_link": event_link,
                "talk_title": talk_title.strip(),
                "session_type": session_type if session_type != "— select —" else "",
                "snowflake_topics": snowflake_topics_selected,
                "support_rank_1": support_rank_1 if support_rank_1 != "— none —" else "",
                "support_rank_2": support_rank_2 if support_rank_2 != "— none —" else "",
                "support_rank_3": support_rank_3 if support_rank_3 != "— none —" else "",
                "estimated_cost": int(estimated_cost),
                "traveling_from": traveling_from.strip(),
                "additional_notes": additional_notes.strip(),
            }

            with st.spinner("Submitting…"):
                ok = save_submission(payload)

            if ok:
                st.session_state.submitted = True
                st.rerun()
            else:
                st.warning(
                    "Could not save your submission. Please try again or contact the Snowflake Community team directly."
                )
