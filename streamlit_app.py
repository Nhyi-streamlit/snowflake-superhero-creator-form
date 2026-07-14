import json
import os
import uuid
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2 import service_account

st.set_page_config(
    page_title="Conference Support — Data Superheroes & Streamlit Creators",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  [data-testid="collapsedControl"] { display: none; }
  section[data-testid="stSidebar"] { display: none; }

  .page-hero {
    background: linear-gradient(135deg, #0E2346 0%, #1B3A6B 60%, #29B5E8 100%);
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

  .identity-card {
    border: 2px solid #E2E8F0;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s;
  }
  .identity-card.active { border-color: #29B5E8; background: #EBF8FF; }

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


# ── Google Sheets writer ──────────────────────────────────────────────────────

def _resolve_creds_info() -> dict:
    """Return service account dict from secrets.toml (local) or env var (HuggingFace/Cloud)."""
    # Local dev / Streamlit Community Cloud — secrets.toml
    try:
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass
    # HuggingFace Spaces / any host — GCP_SERVICE_ACCOUNT_JSON env var (full JSON string)
    raw = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "")
    if raw:
        return json.loads(raw)
    raise RuntimeError(
        "No GCP credentials found. Set [gcp_service_account] in secrets.toml "
        "or the GCP_SERVICE_ACCOUNT_JSON environment variable."
    )


def _resolve_sheet_id() -> tuple[str, str]:
    """Return (spreadsheet_id, worksheet_name)."""
    try:
        return (
            st.secrets["google_sheets"]["spreadsheet_id"],
            st.secrets["google_sheets"].get("worksheet", "Submissions"),
        )
    except Exception:
        pass
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        raise RuntimeError(
            "No sheet ID found. Set [google_sheets] in secrets.toml "
            "or the GOOGLE_SHEET_ID environment variable."
        )
    return sheet_id, os.environ.get("GOOGLE_SHEET_WORKSHEET", "Submissions")


@st.cache_resource
def _get_gspread_client():
    creds_info = _resolve_creds_info()
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    return gspread.authorize(creds)


def _get_worksheet():
    client = _get_gspread_client()
    spreadsheet_id, worksheet_name = _resolve_sheet_id()
    return client.open_by_key(spreadsheet_id).worksheet(worksheet_name)


def save_to_sheets(data: dict) -> bool:
    try:
        ws = _get_worksheet()
        row = [
            data["submission_id"],
            data["submitted_at"],
            data["first_name"],
            data["last_name"],
            data["email"],
            data["job_title"],
            data["company"],
            data["country"],
            data["linkedin_url"],
            data["github_username"],
            data["twitter_handle"],
            data["website_url"],
            # Community identity
            data["community_identity"],
            data["superhero_profile_url"],
            data["streamlit_creator_profile_url"],
            data["snowflake_community_username"],
            data["years_snowflake"],
            # Audience reach
            data["linkedin_followers"],
            data["twitter_followers"],
            data["youtube_subscribers"],
            data["newsletter_subscribers"],
            data["github_stars"],
            data["other_reach_notes"],
            # Past involvement
            data["past_talks_count"],
            data["past_content_summary"],
            data["notable_projects"],
            # Conference
            data["conference_name"],
            data["conference_website"],
            data["conference_type"],
            str(data["conference_start"]),
            str(data["conference_end"]),
            data["conference_city"],
            data["conference_country"],
            data["conference_format"],
            # Talk
            data["talk_title"],
            data["session_type"],
            data["talk_abstract"],
            json.dumps(data["snowflake_topics"]),
            data["acceptance_status"],
            # Support
            json.dumps(data["support_types"]),
            data["estimated_cost"],
            data["traveling_from"],
            data["additional_notes"],
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Could not save to Google Sheets: {e}")
        return False


# ── Session state ─────────────────────────────────────────────────────────────
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ── Success screen ────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown("""
<div class="success-box">
  <div style="font-size:3.5rem; margin-bottom:20px;">🦸</div>
  <h2>You're on our radar!</h2>
  <p>Thanks for letting us know — the Snowflake Developer Relations team<br>
  will review your submission and be in touch soon.</p>
</div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div class="eyebrow">Snowflake DevRel · Community Support</div>
  <h1>Conference Support for Data Superheroes<br>& Streamlit Creators</h1>
  <p>Are you a recognized Snowflake Data Superhero or Streamlit Creator heading to a conference?
  We want to help. Fill out this form so our Developer Relations team can assess how to best support you.</p>
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


# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("conference_support_form", clear_on_submit=False):

    # ── Section 1: About You ──────────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 1 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">About You</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Basic contact info so we can follow up with you.</p>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        first_name = st.text_input("First name *", placeholder="Aba")
        email = st.text_input("Email address *", placeholder="you@example.com")
        company = st.text_input("Company / Organization", placeholder="Acme Corp")
        linkedin_url = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/yourprofile")
        twitter_handle = st.text_input("Twitter / X handle", placeholder="@yourhandle")
    with a2:
        last_name = st.text_input("Last name *", placeholder="Micah")
        job_title = st.text_input("Job title / Role", placeholder="Data Engineer")
        country = st.selectbox("Country *", ["— select —"] + COUNTRIES)
        github_username = st.text_input("GitHub username", placeholder="yourusername")
        website_url = st.text_input("Personal website / blog", placeholder="https://yourblog.dev")

    st.divider()

    # ── Section 2: Community Identity ────────────────────────────────────────
    st.markdown('<span class="step-label">Section 2 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Community Identity</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us which Snowflake community program(s) you\'re part of.</p>', unsafe_allow_html=True)

    community_identity = st.multiselect(
        "I am a... *  (select all that apply)",
        ["Snowflake Data Superhero", "Streamlit Creator", "Both"],
        placeholder="Select your community identity",
    )

    ci1, ci2 = st.columns(2)
    with ci1:
        superhero_profile_url = st.text_input(
            "Data Superhero profile URL",
            placeholder="https://community.snowflake.com/s/profile/...",
            help="Link to your Snowflake Community profile page showing the Superhero badge.",
        )
        snowflake_community_username = st.text_input(
            "Snowflake Community Forum username",
            placeholder="your-forum-handle",
        )
    with ci2:
        streamlit_creator_profile_url = st.text_input(
            "Streamlit Creators profile URL",
            placeholder="https://streamlit.io/creators/...",
            help="Link to your profile on the Streamlit Creators page.",
        )
        years_snowflake = st.select_slider(
            "Years working with Snowflake",
            options=["< 6 months", "6–12 months", "1–2 years", "2–4 years", "4+ years"],
            value="1–2 years",
        )

    st.divider()

    # ── Section 3: Audience Reach ─────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 3 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Audience Reach</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Approximate numbers are fine — this helps us understand your community footprint.</p>', unsafe_allow_html=True)

    ar1, ar2, ar3 = st.columns(3)
    with ar1:
        linkedin_followers = st.number_input("LinkedIn followers", min_value=0, step=100, value=0)
        youtube_subscribers = st.number_input("YouTube subscribers", min_value=0, step=100, value=0)
    with ar2:
        twitter_followers = st.number_input("Twitter / X followers", min_value=0, step=100, value=0)
        newsletter_subscribers = st.number_input("Newsletter subscribers", min_value=0, step=100, value=0)
    with ar3:
        github_stars = st.number_input("Total GitHub stars (across repos)", min_value=0, step=10, value=0)
        st.markdown("")  # spacer

    other_reach_notes = st.text_input(
        "Other channels / reach notes",
        placeholder="e.g. 5k Discord members, Podcast with 2k monthly listeners",
    )

    st.divider()

    # ── Section 4: Past Snowflake Involvement ─────────────────────────────────
    st.markdown('<span class="step-label">Section 4 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Past Snowflake Involvement</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Share what you\'ve built, written, or presented on Snowflake topics.</p>', unsafe_allow_html=True)

    pi1, pi2 = st.columns(2)
    with pi1:
        past_talks_count = st.selectbox(
            "Snowflake-related talks / sessions given (lifetime)",
            ["0", "1–2", "3–5", "6–10", "10+"],
        )
    with pi2:
        st.markdown("")  # spacer

    past_content_summary = st.text_area(
        "Notable content, blog posts, or videos you've created about Snowflake",
        placeholder="e.g. 'Built a 3-part YouTube series on Streamlit in Snowflake (15k views total)', or links to blog posts...",
        height=110,
    )
    notable_projects = st.text_area(
        "Notable open-source projects or community contributions related to Snowflake",
        placeholder="GitHub repos, Streamlit apps, community tools, etc. — include links if you have them.",
        height=90,
    )

    st.divider()

    # ── Section 5: The Conference ──────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 5 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">The Conference</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us about the event you\'re attending or planning to attend.</p>', unsafe_allow_html=True)

    conference_name = st.text_input("Conference name *", placeholder="PyCon US 2025")
    cf1, cf2 = st.columns(2)
    with cf1:
        conference_website = st.text_input("Conference website", placeholder="https://us.pycon.org")
        conference_type = st.selectbox(
            "Conference type",
            ["— select —", "Developer / Tech Conference", "Data & AI Conference", "Open Source Event",
             "Streamlit Community Event", "Academic / University", "Meetup / Local Event", "Other"],
        )
        conference_start = st.date_input("Start date")
        conference_city = st.text_input("City", placeholder="Pittsburgh")
    with cf2:
        conference_format = st.radio("Format", ["In-person", "Hybrid", "Virtual"], horizontal=True)
        st.markdown("")
        conference_end = st.date_input("End date")
        conference_country = st.selectbox("Country", ["— select —"] + COUNTRIES)

    st.divider()

    # ── Section 6: Support Request ────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 6 of 6</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Talk & Support Request</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us what you\'ll be presenting and what kind of support would help most.</p>', unsafe_allow_html=True)

    talk_title = st.text_input(
        "Talk / session title",
        placeholder="Building Production AI Agents on Snowflake",
        help="Leave blank if you haven't finalized a title yet.",
    )
    sr_c1, sr_c2 = st.columns(2)
    with sr_c1:
        session_type = st.selectbox(
            "Session type",
            ["— select —", "Keynote", "Talk (30–45 min)", "Lightning Talk (5–15 min)",
             "Workshop / Tutorial", "Panel", "Poster / Demo", "Not yet confirmed", "Other"],
        )
        acceptance_status = st.selectbox(
            "Acceptance status",
            ["— select —", "Accepted to speak", "CFP submitted — awaiting decision",
             "Planning to submit a CFP", "Invited / confirmed by organizers", "Attending as an attendee only"],
        )
    with sr_c2:
        snowflake_topics_selected = st.multiselect(
            "Snowflake topics you'll cover (if speaking)",
            SNOWFLAKE_TOPICS,
        )

    talk_abstract = st.text_area(
        "Talk abstract or description",
        placeholder="A brief summary of what you'll be presenting — a draft is totally fine.",
        height=130,
    )

    st.markdown("**What support are you looking for?**")
    support_types = st.multiselect(
        "Select all that apply",
        ["Travel grant (flights / ground transport)", "Hotel / accommodation",
         "Conference registration / ticket", "Speaker coaching",
         "Talk / slide deck feedback", "Social amplification",
         "DevRel introduction or co-presentation", "Snowflake swag / materials"],
        placeholder="Pick one or more support types",
    )

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
        placeholder="Additional context, timing constraints, co-presenters, past DevRel interactions, etc.",
        height=100,
    )

    st.space("small")

    with st.container(border=True):
        st.caption(
            "By submitting this form you agree to be contacted by the Snowflake Developer Relations team "
            "regarding conference support. Your information will only be used to evaluate and manage this program."
        )
        submitted = st.form_submit_button(
            "Submit — Let us know you're going →",
            type="primary",
            use_container_width=True,
        )

    # ── Validation & submit ───────────────────────────────────────────────────
    if submitted:
        errors = []
        if not first_name.strip():
            errors.append("First name is required.")
        if not last_name.strip():
            errors.append("Last name is required.")
        if not email.strip() or "@" not in email:
            errors.append("A valid email address is required.")
        if country == "— select —":
            errors.append("Please select your country.")
        if not community_identity:
            errors.append("Please select your community identity (Section 2).")
        if not conference_name.strip():
            errors.append("Conference name is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            payload = {
                "submission_id": str(uuid.uuid4()),
                "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip(),
                "job_title": job_title.strip(),
                "company": company.strip(),
                "country": country if country != "— select —" else "",
                "linkedin_url": linkedin_url.strip(),
                "github_username": github_username.strip(),
                "twitter_handle": twitter_handle.strip(),
                "website_url": website_url.strip(),
                "community_identity": ", ".join(community_identity),
                "superhero_profile_url": superhero_profile_url.strip(),
                "streamlit_creator_profile_url": streamlit_creator_profile_url.strip(),
                "snowflake_community_username": snowflake_community_username.strip(),
                "years_snowflake": years_snowflake,
                "linkedin_followers": int(linkedin_followers),
                "twitter_followers": int(twitter_followers),
                "youtube_subscribers": int(youtube_subscribers),
                "newsletter_subscribers": int(newsletter_subscribers),
                "github_stars": int(github_stars),
                "other_reach_notes": other_reach_notes.strip(),
                "past_talks_count": past_talks_count,
                "past_content_summary": past_content_summary.strip(),
                "notable_projects": notable_projects.strip(),
                "conference_name": conference_name.strip(),
                "conference_website": conference_website.strip(),
                "conference_type": conference_type if conference_type != "— select —" else "",
                "conference_start": conference_start,
                "conference_end": conference_end,
                "conference_city": conference_city.strip(),
                "conference_country": conference_country if conference_country != "— select —" else "",
                "conference_format": conference_format,
                "talk_title": talk_title.strip(),
                "session_type": session_type if session_type != "— select —" else "",
                "talk_abstract": talk_abstract.strip(),
                "snowflake_topics": snowflake_topics_selected,
                "acceptance_status": acceptance_status if acceptance_status != "— select —" else "",
                "support_types": support_types,
                "estimated_cost": int(estimated_cost),
                "traveling_from": traveling_from.strip(),
                "additional_notes": additional_notes.strip(),
            }

            with st.spinner("Submitting…"):
                ok = save_to_sheets(payload)

            if ok:
                st.session_state.submitted = True
                st.rerun()
            else:
                st.warning(
                    "Could not save to Google Sheets — please check your secrets configuration. "
                    "Contact the program team directly if this issue persists."
                )
