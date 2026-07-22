import os
import uuid
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Event Support — Data Superheroes & Streamlit Creators",
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
    background: rgba(41,181,232,0.25);
    color: #7ED8F6;
    border: 1px solid rgba(41,181,232,0.4);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 16px;
  }
  .page-hero h1 { color: #FFFFFF; font-size: 2.1rem; font-weight: 800; line-height: 1.2; margin-bottom: 10px; }
  .page-hero p  { color: #A8D8F0; font-size: 1rem; max-width: 640px; margin: 0; }

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
    margin-bottom: 8px;
  }
  .section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0E2346;
    margin-top: 2px;
    margin-bottom: 2px;
  }
  .section-hint { font-size: 0.87rem; color: #718096; margin-bottom: 18px; }

  .success-box {
    background: linear-gradient(135deg, #0E2346, #1B3A6B);
    border-radius: 16px;
    padding: 72px 48px;
    text-align: center;
  }
  .success-box h2 { color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 10px; }
  .success-box p  { color: #A8D8F0; font-size: 1rem; margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)


# ── Snowflake writer ──────────────────────────────────────────────────────────

def _get_sheets_access_token(refresh_token: str, client_id: str, client_secret: str) -> str:
    """Exchange refresh token for a fresh access token."""
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
    """Append form submission as a row to Google Sheets, with GitHub Issues as fallback."""
    import requests

    # ── Primary: Google Sheets ─────────────────────────────────────────────────
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

    if all([refresh_token, client_id, client_secret, spreadsheet_id]):
        try:
            access_token = _get_sheets_access_token(refresh_token, client_id, client_secret)
            row = [
                data.get("submission_id", ""),
                data.get("submitted_at", ""),
                data.get("first_name", ""),
                data.get("last_name", ""),
                data.get("email", ""),
                data.get("country", ""),
                data.get("city", ""),
                data.get("community_identity", ""),
                str(data.get("years_snowflake", "")),
                data.get("conference_name", ""),
                data.get("conference_website", ""),
                data.get("talk_title", ""),
                data.get("session_type", ""),
                ", ".join(data.get("snowflake_topics", [])),
                data.get("support_rank_1", ""),
                data.get("support_rank_2", ""),
                data.get("support_rank_3", ""),
                str(data.get("estimated_cost", 0)),
                data.get("traveling_from", ""),
                data.get("preferred_event_types", ""),
                data.get("additional_notes", ""),
            ]
            append_resp = requests.post(
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
                f"/values/Sheet1!A:AB:append",
                params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                json={"values": [row]},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15,
            )
            if append_resp.status_code == 200:
                return True
            st.error(f"Sheets write failed ({append_resp.status_code}): {append_resp.text[:200]}")
            return False
        except Exception as e:
            st.error(f"Sheets submission error: {e}")
            return False

    # ── Fallback: GitHub Issues ────────────────────────────────────────────────
    gh_token = ""
    try:
        gh_token = st.secrets.get("GITHUB_SUBMISSIONS_TOKEN", "")
    except Exception:
        gh_token = os.environ.get("GITHUB_SUBMISSIONS_TOKEN", "")

    if not gh_token:
        st.error("No submission backend configured. Please contact the program team.")
        return False

    title = (
        f"[Form] {data['first_name']} {data['last_name']} "
        f"— {data.get('conference_name', 'Event TBD')}"
    )
    lines = [
        f"**Submission ID:** {data['submission_id']}",
        f"**Submitted At:** {data['submitted_at']}",
        "", "## Contact",
        f"- **Name:** {data['first_name']} {data['last_name']}",
        f"- **Email:** {data['email']}",
        f"- **Job Title:** {data.get('job_title', '')}",
        f"- **Company:** {data.get('company', '')}",
        f"- **Country:** {data.get('country', '')}",
        f"- **LinkedIn:** {data.get('linkedin_url', '')}",
        "", "## Community Identity",
        f"- **Identity:** {data.get('community_identity', '')}",
        f"- **Years with Snowflake:** {data.get('years_snowflake', '')}",
        "", "## Conference",
        f"- **Event:** {data.get('conference_name', '')}",
        f"- **Dates:** {data.get('conference_start', '')} → {data.get('conference_end', '')}",
        f"- **Location:** {data.get('conference_city', '')}, {data.get('conference_country', '')}",
        "", "## Talk & Support",
        f"- **Talk Title:** {data.get('talk_title', '')}",
        f"- **Support Requested:** {', '.join(data.get('support_types', []))}",
        f"- **Est. Travel Cost (USD):** {data.get('estimated_cost', 0)}",
    ]
    try:
        requests.post(
            "https://api.github.com/repos/Nhyi-streamlit/devrel-conference-submissions/issues",
            json={"title": title, "body": "\n".join(lines), "labels": ["submission"]},
            headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
            timeout=15,
        )
        return True
    except Exception:
        return False

def save_interest(data: dict) -> bool:
    """Append interest registration to the 'Interested Speakers' sheet tab."""
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
            data.get("country", ""),
            data.get("city", ""),
            data.get("community_identity", ""),
            ", ".join(data.get("topics", [])),
            ", ".join(data.get("event_types", [])),
            data.get("additional_notes", ""),
        ]
        resp = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            f"/values/Interested%20Speakers!A:K:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [row]},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Submission error: {e}")
        return False


# ── Session state ─────────────────────────────────────────────────────────────
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "interest_submitted" not in st.session_state:
    st.session_state.interest_submitted = False
if "num_events" not in st.session_state:
    st.session_state.num_events = 1


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div style="display:flex; align-items:center; gap:14px; margin-bottom:18px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg"
         alt="Snowflake" height="36"
         style="filter:brightness(0) invert(1); flex-shrink:0;">
    <div class="eyebrow" style="margin-bottom:0;">Snowflake Voices · Community Support</div>
  </div>
  <h1>Snowflake Voices</h1>
  <p>We want to amplify the voices of our Data Superheroes and Streamlit Creators.
  Whether you have an event lined up or just want to get on a stage — we'd love to hear from you.</p>
</div>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────────
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



# ── Success screen ─────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown("""
<div class="success-box">
  <div style="font-size:3.5rem; margin-bottom:20px;">🦸</div>
  <h2>You're on our radar!</h2>
  <p>Thanks for letting us know — the Snowflake Community team<br>
  will review your submission and be in touch soon.</p>
</div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("conference_support_form", clear_on_submit=False):

    # ── Section 1: About You ──────────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 1 of 5</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">About You</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Basic contact info so we can follow up with you.</p>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        first_name = st.text_input("First name", placeholder="Aba")
        country    = st.selectbox("Country", ["— select —"] + COUNTRIES)
        email      = st.text_input("Email address", placeholder="you@example.com")
    with a2:
        last_name = st.text_input("Last name", placeholder="Micah")
        city      = st.text_input("City", placeholder="San Francisco")

    # removed fields — kept as empty strings for payload compatibility
    company = ""
    job_title = ""
    linkedin_url = ""

    st.divider()

    # ── Section 2: Community Identity ─────────────────────────────────────────
    st.markdown('<span class="step-label">Section 2 of 5</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Community Identity</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us which Snowflake community program(s) you\'re part of.</p>', unsafe_allow_html=True)

    community_identity = st.multiselect(
        "I am a... (select all that apply)",
        ["Snowflake Data Superhero", "Streamlit Creator", "Both"],
        placeholder="Select your community identity",
    )

    years_snowflake = st.select_slider(
        "Years working with Snowflake",
        options=["< 6 months", "6–12 months", "1–2 years", "2–4 years", "4+ years"],
        value="1–2 years",
    )

    st.divider()

    # ── Section 3: Event or Interest ──────────────────────────────────────────
    st.markdown('<span class="step-label">Section 3 of 5</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Are you heading to an event, or looking to speak?</p>', unsafe_allow_html=True)

    s3_event, s3_interest = st.tabs(["📅  I have an event and I'm looking for support", "🙋  I don't have an event but I want to speak"])

    with s3_event:
        st.markdown('<p class="section-title" style="margin-top:16px;">The Event</p>', unsafe_allow_html=True)
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

        st.divider()

        # ── Section 4 (event path only): Your Talk ───────────────────────────
        st.markdown('<span class="step-label">Section 4 of 5</span>', unsafe_allow_html=True)
        st.markdown('<p class="section-title">Your Talk</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Tell us what you may be presenting. No worries if the details are still taking shape.</p>', unsafe_allow_html=True)

        talk_title = st.text_input(
            "Talk / session title",
            placeholder="Building Production AI Agents on Snowflake",
        )
        st.caption("If you know, no worries if you don't.")

        sr_c1, sr_c2 = st.columns(2)
        with sr_c1:
            session_type = st.selectbox(
                "Session type",
                ["— select —", "Keynote", "Talk (30–45 min)", "Lightning Talk (5–15 min)",
                 "Workshop / Tutorial", "Panel", "Poster / Demo", "Not yet confirmed", "Other"],
            )
            st.caption("If you know, no worries if you don't.")
            acceptance_status = ""
        with sr_c2:
            snowflake_topics_selected = st.multiselect(
                "Snowflake topics you'll cover (or want to speak about)",
                SNOWFLAKE_TOPICS,
            )

        talk_abstract = ""

    with s3_interest:
        st.markdown('<p class="section-title" style="margin-top:16px;">Interested in speaking but no event lined up yet?</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Let us know what kinds of events you\'d be open to — we\'re working with local partners to create opportunities in 14 countries.</p>', unsafe_allow_html=True)

        preferred_event_types = st.multiselect(
            "Types of events you would be open to speaking at",
            ["Meetup / Local event", "Regional conference", "Workshop / Tutorial",
             "Hackathon", "Online / Virtual event", "Any"],
            key="preferred_event_types",
        )

        add_event_btn = False  # not used in this path
        # safe defaults for talk fields (not shown in this tab)
        talk_title = ""
        session_type = "— select —"
        snowflake_topics_selected = []
        talk_abstract = ""
        acceptance_status = ""

    # ── Compute event payload values (safe defaults if interest tab used) ──────
    try:
        conference_name    = " | ".join(e[0] for e in event_entries if e[0].strip())
        conference_website = " | ".join(e[1] for e in event_entries if e[1].strip())
    except NameError:
        conference_name = ""
        conference_website = ""
    try:
        preferred_event_types
    except NameError:
        preferred_event_types = []

    # kept in payload for Sheet compatibility
    conference_type = conference_start = conference_end = ""
    conference_city = conference_country = conference_format = ""

    st.divider()

    # ── Section 5: Support ────────────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 5 of 5</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">What Support Are You Looking For?</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Rank your top 3 priorities and we will work from there.</p>', unsafe_allow_html=True)

    SUPPORT_OPTIONS = [
        "— none —",
        "Travel grant (flights / ground transport)",
        "Hotel / accommodation",
        "Event registration / ticket",
        "Speaker coaching",
        "Talk / slide deck feedback",
        "Social amplification",
        "Snowflake Community introduction or co-presentation",
        "Snowflake swag / materials",
    ]
    rk1, rk2, rk3 = st.columns(3)
    with rk1:
        support_rank_1 = st.selectbox("1st priority", SUPPORT_OPTIONS, index=0)
    with rk2:
        support_rank_2 = st.selectbox("2nd priority", SUPPORT_OPTIONS, index=0)
    with rk3:
        support_rank_3 = st.selectbox("3rd priority", SUPPORT_OPTIONS, index=0)
    support_types = [s for s in [support_rank_1, support_rank_2, support_rank_3] if s != "— none —"]

    sup1, sup2 = st.columns(2)
    with sup1:
        estimated_cost = st.number_input(
            "Estimated travel cost (USD)",
            min_value=0, max_value=25000, step=50, value=500,
            help="Rough estimate — flights + hotel if applicable.",
        )
    with sup2:
        traveling_from = st.text_input("Traveling from (city, country)", placeholder="Lagos, Nigeria")

    additional_notes = st.text_area(
        "Anything else you'd like us to know?",
        placeholder="Additional context, timing constraints, co-presenters, past Snowflake Community interactions, etc.",
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
        payload = {
            "submission_id": str(uuid.uuid4()),
            "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip(),
            "country": country if country != "— select —" else "",
            "city": city.strip(),
            "community_identity": ", ".join(community_identity),
            "years_snowflake": years_snowflake,
            "conference_name": conference_name.strip(),
            "conference_website": conference_website.strip(),
            "talk_title": talk_title.strip(),
            "session_type": session_type if session_type != "— select —" else "",
            "snowflake_topics": snowflake_topics_selected,
            "support_rank_1": support_rank_1 if support_rank_1 != "— none —" else "",
            "support_rank_2": support_rank_2 if support_rank_2 != "— none —" else "",
            "support_rank_3": support_rank_3 if support_rank_3 != "— none —" else "",
            "estimated_cost": int(estimated_cost),
            "traveling_from": traveling_from.strip(),
            "preferred_event_types": ", ".join(preferred_event_types),
            "additional_notes": additional_notes.strip(),
        }

        with st.spinner("Submitting…"):
            ok = save_submission(payload)

        if ok:
            st.session_state.submitted = True
            st.rerun()
        else:
            st.warning(
                "Could not save your submission. Please try again or contact the program team directly."
            )
