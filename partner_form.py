import os
import uuid
from datetime import datetime, date

import streamlit as st

st.set_page_config(
    page_title="Snowflake Community Voices — Partner Metrics",
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

  .page-hero {
    background: #0E2346;
    padding: 36px 48px;
    border-radius: 14px;
    margin-bottom: 32px;
    border-left: 6px solid #29B5E8;
  }
  .page-hero h1 { color: #fff; font-size: 1.7rem; font-weight: 800; margin: 0 0 6px; }
  .page-hero p  { color: rgba(255,255,255,0.75); margin: 0; font-size: 0.92rem; }

  .section-header {
    font-size: 0.95rem; font-weight: 700; color: #0E2346;
    border-left: 4px solid #29B5E8; padding-left: 10px;
    margin: 28px 0 14px;
  }

  .success-box {
    background: #F0FFF4; border: 2px solid #C6F6D5; border-radius: 14px;
    padding: 40px; text-align: center; margin: 40px auto; max-width: 600px;
  }
  .success-box h2 { color: #22543D; font-size: 1.5rem; }
  .success-box p  { color: #2F855A; }
</style>
""", unsafe_allow_html=True)


# ── Auth ───────────────────────────────────────────────────────────────────────
def _get_access_token(refresh_token, client_id, client_secret):
    import requests
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }, timeout=10)
    return resp.json().get("access_token", "")


def save_metrics(data: dict) -> bool:
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
        st.error("Backend not configured.")
        return False

    try:
        access_token = _get_access_token(refresh_token, client_id, client_secret)
        row = [
            data.get("submission_id", ""),
            data.get("submitted_at", ""),
            data.get("partner", ""),
            data.get("event_name", ""),
            data.get("city", ""),
            data.get("event_date", ""),
            data.get("format", ""),
            data.get("event_url", ""),
            data.get("total_attendees", ""),
            data.get("registered_rsvps", ""),
            data.get("practitioner_pct", ""),
            data.get("speaker_name", ""),
            data.get("talk_title", ""),
            data.get("session_type", ""),
            data.get("audience_score", ""),
            data.get("qr_scans", ""),
            data.get("top_topic", ""),
            data.get("trial_signups", ""),
            data.get("snowflake_demoed", ""),
            data.get("products_featured", ""),
            data.get("social_posts", ""),
            data.get("social_reach", ""),
            data.get("highlights", ""),
            data.get("improvements", ""),
            data.get("partner_again", ""),
        ]
        resp = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            "/values/Partner%20Metrics!A:Y:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [row]},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Submission error: {e}")
        return False


# ── Session state ──────────────────────────────────────────────────────────────
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div style="display:flex; align-items:center; gap:14px; margin-bottom:14px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg"
         alt="Snowflake" height="32" style="filter:brightness(0) invert(1); flex-shrink:0;">
    <span style="color:#29B5E8; font-size:0.8rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">
      Partner · Snowflake Community Voices
    </span>
  </div>
  <h1>Event Metrics Report</h1>
  <p>Submit post-event data so the Snowflake Community team can track program impact,
  measure speaker performance, and improve future events.</p>
</div>
""", unsafe_allow_html=True)

# ── Success screen ─────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown("""
<div class="success-box">
  <div style="font-size:3rem; margin-bottom:16px;">✅</div>
  <h2>Metrics received — thank you!</h2>
  <p>The Snowflake Community team will review your submission<br>and follow up within 5 business days.</p>
</div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Form ───────────────────────────────────────────────────────────────────────
with st.form("partner_metrics_form", clear_on_submit=False):

    # ── Section 1: Partner & Event Details ────────────────────────────────────
    st.markdown('<div class="section-header">Section 1 — Partner & Event Details</div>', unsafe_allow_html=True)

    p1c1, p1c2 = st.columns(2)
    with p1c1:
        partner = st.selectbox("Partner organisation *", ["— select —", "AI Camp", "ODSC"])
        event_name = st.text_input("Event name *", placeholder="AI Meetup (London) — September 2026")
        event_date = st.date_input("Event date *", value=date.today())
    with p1c2:
        city = st.text_input("City *", placeholder="London, UK")
        event_format = st.selectbox("Format", ["In-person", "Virtual", "Hybrid"])
        event_url = st.text_input("Event URL (optional)", placeholder="https://luma.com/...")

    st.divider()

    # ── Section 2: Attendance ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Section 2 — Attendance</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        total_attendees = st.number_input("Total attendees (actual)", min_value=0, value=0, step=1)
    with a2:
        registered_rsvps = st.number_input("Registered RSVPs", min_value=0, value=0, step=1)
    with a3:
        practitioner_pct = st.selectbox(
            "Audience — % data/AI practitioners (est.)",
            ["— select —", "Under 25%", "25–50%", "50–75%", "75–90%", "90%+"]
        )

    st.divider()

    # ── Section 3: Speaker Performance ────────────────────────────────────────
    st.markdown('<div class="section-header">Section 3 — Speaker Performance</div>', unsafe_allow_html=True)
    st.caption("Complete one section per speaker. If multiple speakers, submit a separate report for each.")

    s1, s2 = st.columns(2)
    with s1:
        speaker_name  = st.text_input("Speaker name *")
        talk_title    = st.text_input("Talk title *")
        session_type  = st.selectbox("Session type",
            ["— select —", "Keynote", "Talk (30–45 min)", "Lightning Talk", "Workshop / Tutorial", "Panel", "Demo"])
    with s2:
        audience_score = st.slider(
            "Audience feedback score (1 = poor, 5 = excellent)", 1, 5, 4,
            help="Use the average score from QR code feedback, verbal poll, or organiser estimate."
        )
        qr_scans = st.number_input("QR code scans (est.)", min_value=0, value=0, step=1,
            help="Approximate number of audience members who scanned the feedback QR code.")
        top_topic = st.text_input("Top topic that resonated with the audience",
            placeholder="e.g. Cortex AI agent demo, production deployment patterns")

    st.divider()

    # ── Section 4: Snowflake Impact ───────────────────────────────────────────
    st.markdown('<div class="section-header">Section 4 — Snowflake Impact</div>', unsafe_allow_html=True)

    i1, i2 = st.columns(2)
    with i1:
        trial_signups = st.number_input("Snowflake trial sign-ups generated (est.)", min_value=0, value=0, step=1,
            help="Include QR code scans to the trial link if tracked.")
        snowflake_demoed = st.selectbox("Was Snowflake demoed live?", ["Yes — live demo", "Yes — recorded demo", "Mentioned but no demo", "Not mentioned"])
        products_featured = st.multiselect(
            "Snowflake products featured",
            ["Cortex AI / LLM Functions", "Cortex Analyst", "Cortex Search", "Cortex Code (CoCo)",
             "Snowpark", "Streamlit in Snowflake", "Dynamic Tables", "Data Sharing / Marketplace",
             "Iceberg Tables", "Native Apps", "Other"],
        )
    with i2:
        social_posts = st.number_input("Social posts made (by speaker + organiser combined)", min_value=0, value=0, step=1)
        social_reach = st.number_input("Estimated social impressions", min_value=0, value=0, step=1,
            help="Sum of LinkedIn + X impressions from all posts about the event.")

    st.divider()

    # ── Section 5: Feedback & Notes ───────────────────────────────────────────
    st.markdown('<div class="section-header">Section 5 — Feedback & Notes</div>', unsafe_allow_html=True)

    highlights    = st.text_area("Event highlights — what went particularly well?", height=100,
        placeholder="Strong Q&A, packed house, great audience questions about Cortex AI...")
    improvements  = st.text_area("What could be improved for next time?", height=80,
        placeholder="More time for the demo, better AV setup, earlier promotion...")
    partner_again = st.selectbox("Would you like to partner with Snowflake Community Voices again?",
        ["— select —", "Yes — definitely", "Yes — with some adjustments", "Undecided", "Not at this time"])

    st.divider()

    submitted = st.form_submit_button(
        "Submit Metrics Report →",
        type="primary",
        use_container_width=True,
    )

# ── Handler ────────────────────────────────────────────────────────────────────
if submitted:
    errors = []
    if partner == "— select —": errors.append("Partner organisation")
    if not event_name.strip():  errors.append("Event name")
    if not city.strip():        errors.append("City")
    if not speaker_name.strip():errors.append("Speaker name")
    if not talk_title.strip():  errors.append("Talk title")

    if errors:
        st.error(f"Please fill in required fields: {', '.join(errors)}")
    else:
        payload = {
            "submission_id":   str(uuid.uuid4()),
            "submitted_at":    datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "partner":         partner,
            "event_name":      event_name.strip(),
            "city":            city.strip(),
            "event_date":      str(event_date),
            "format":          event_format,
            "event_url":       event_url.strip(),
            "total_attendees": str(total_attendees),
            "registered_rsvps":str(registered_rsvps),
            "practitioner_pct":practitioner_pct if practitioner_pct != "— select —" else "",
            "speaker_name":    speaker_name.strip(),
            "talk_title":      talk_title.strip(),
            "session_type":    session_type if session_type != "— select —" else "",
            "audience_score":  str(audience_score),
            "qr_scans":        str(qr_scans),
            "top_topic":       top_topic.strip(),
            "trial_signups":   str(trial_signups),
            "snowflake_demoed":snowflake_demoed,
            "products_featured": ", ".join(products_featured),
            "social_posts":    str(social_posts),
            "social_reach":    str(social_reach),
            "highlights":      highlights.strip(),
            "improvements":    improvements.strip(),
            "partner_again":   partner_again if partner_again != "— select —" else "",
        }

        with st.spinner("Submitting…"):
            ok = save_metrics(payload)

        if ok:
            st.session_state.submitted = True
            st.rerun()
        else:
            st.warning("Could not save your report. Please try again.")
