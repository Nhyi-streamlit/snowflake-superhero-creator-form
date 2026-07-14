import json
import os
import uuid
from datetime import datetime

import streamlit as st

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

def _get_sf_session():
    """Return a Snowflake session/cursor. Tries st.connection first, then env vars."""
    try:
        conn = st.connection("snowflake")
        return conn.session(), None
    except Exception:
        pass
    try:
        import snowflake.connector
        sf = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "MARKETING_ADHOC"),
            database="MARKETING",
            schema="PLAYGROUND",
            role=os.environ.get("SNOWFLAKE_ROLE", "MARKETING_SENSITIVE_RO"),
        )
        return sf.cursor(), sf.close
    except Exception:
        return None, None


def save_submission(data: dict) -> bool:
    obj, cleanup = _get_sf_session()
    if obj is None:
        return False

    SQL = """
        INSERT INTO MARKETING.PLAYGROUND.SUPERHERO_CREATOR_CONF_SUBMISSIONS (
            SUBMISSION_ID, SUBMITTED_AT,
            FIRST_NAME, LAST_NAME, EMAIL, JOB_TITLE, COMPANY, COUNTRY,
            LINKEDIN_URL, GITHUB_USERNAME, TWITTER_HANDLE, WEBSITE_URL,
            COMMUNITY_IDENTITY, SUPERHERO_PROFILE_URL, STREAMLIT_CREATOR_PROFILE_URL,
            SNOWFLAKE_COMMUNITY_USERNAME, YEARS_SNOWFLAKE,
            LINKEDIN_FOLLOWERS, TWITTER_FOLLOWERS, YOUTUBE_SUBSCRIBERS,
            NEWSLETTER_SUBSCRIBERS, GITHUB_STARS, OTHER_REACH_NOTES,
            PAST_TALKS_COUNT, PAST_CONTENT_SUMMARY, NOTABLE_PROJECTS,
            CONFERENCE_NAME, CONFERENCE_WEBSITE, CONFERENCE_TYPE,
            CONFERENCE_START_DATE, CONFERENCE_END_DATE,
            CONFERENCE_CITY, CONFERENCE_COUNTRY, CONFERENCE_FORMAT,
            TALK_TITLE, SESSION_TYPE, TALK_ABSTRACT, SNOWFLAKE_TOPICS,
            ACCEPTANCE_STATUS, SUPPORT_TYPES, ESTIMATED_COST_USD,
            TRAVELING_FROM, ADDITIONAL_NOTES
        ) VALUES (
            :sub_id, :submitted_at,
            :first_name, :last_name, :email, :job_title, :company, :country,
            :linkedin_url, :github_username, :twitter_handle, :website_url,
            :community_identity, :superhero_url, :streamlit_url,
            :sf_community_username, :years_snowflake,
            :linkedin_followers, :twitter_followers, :youtube_subscribers,
            :newsletter_subscribers, :github_stars, :other_reach_notes,
            :past_talks_count, :past_content_summary, :notable_projects,
            :conference_name, :conference_website, :conference_type,
            :conference_start, :conference_end,
            :conference_city, :conference_country, :conference_format,
            :talk_title, :session_type, :talk_abstract, PARSE_JSON(:snowflake_topics),
            :acceptance_status, PARSE_JSON(:support_types), :estimated_cost,
            :traveling_from, :additional_notes
        )
    """

    params = {
        "sub_id": data["submission_id"],
        "submitted_at": data["submitted_at"],
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "job_title": data.get("job_title", ""),
        "company": data.get("company", ""),
        "country": data.get("country", ""),
        "linkedin_url": data.get("linkedin_url", ""),
        "github_username": data.get("github_username", ""),
        "twitter_handle": data.get("twitter_handle", ""),
        "website_url": data.get("website_url", ""),
        "community_identity": data.get("community_identity", ""),
        "superhero_url": data.get("superhero_profile_url", ""),
        "streamlit_url": data.get("streamlit_creator_profile_url", ""),
        "sf_community_username": data.get("snowflake_community_username", ""),
        "years_snowflake": data.get("years_snowflake", ""),
        "linkedin_followers": data.get("linkedin_followers", 0),
        "twitter_followers": data.get("twitter_followers", 0),
        "youtube_subscribers": data.get("youtube_subscribers", 0),
        "newsletter_subscribers": data.get("newsletter_subscribers", 0),
        "github_stars": data.get("github_stars", 0),
        "other_reach_notes": data.get("other_reach_notes", ""),
        "past_talks_count": data.get("past_talks_count", "0"),
        "past_content_summary": data.get("past_content_summary", ""),
        "notable_projects": data.get("notable_projects", ""),
        "conference_name": data["conference_name"],
        "conference_website": data.get("conference_website", ""),
        "conference_type": data.get("conference_type", ""),
        "conference_start": str(data.get("conference_start", "")),
        "conference_end": str(data.get("conference_end", "")),
        "conference_city": data.get("conference_city", ""),
        "conference_country": data.get("conference_country", ""),
        "conference_format": data.get("conference_format", ""),
        "talk_title": data.get("talk_title", ""),
        "session_type": data.get("session_type", ""),
        "talk_abstract": data.get("talk_abstract", ""),
        "snowflake_topics": json.dumps(data.get("snowflake_topics", [])),
        "acceptance_status": data.get("acceptance_status", ""),
        "support_types": json.dumps(data.get("support_types", [])),
        "estimated_cost": float(data.get("estimated_cost", 0) or 0),
        "traveling_from": data.get("traveling_from", ""),
        "additional_notes": data.get("additional_notes", ""),
    }

    try:
        import snowflake.snowpark
        if isinstance(obj, snowflake.snowpark.Session):
            obj.sql(SQL, params=params).collect()
            return True
    except Exception:
        pass

    try:
        obj.execute(SQL, params)
        obj.connection.commit()
        return True
    except Exception as e:
        st.error(f"Could not save submission: {e}")
        if cleanup:
            cleanup()
        return False

    if cleanup:
        cleanup()
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
    st.markdown('<span class="step-label">Section 1 of 4</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">About You</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Basic contact info so we can follow up with you.</p>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        first_name = st.text_input("First name *", placeholder="Aba")
        email = st.text_input("Email address *", placeholder="you@example.com")
        company = st.text_input("Company / Organization", placeholder="Acme Corp")
        linkedin_url = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/yourprofile")
    with a2:
        last_name = st.text_input("Last name *", placeholder="Micah")
        job_title = st.text_input("Job title / Role", placeholder="Data Engineer")
        country = st.selectbox("Country *", ["— select —"] + COUNTRIES)

    st.divider()

    # ── Section 2: Community Identity ────────────────────────────────────────
    st.markdown('<span class="step-label">Section 2 of 4</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Community Identity</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us which Snowflake community program(s) you\'re part of.</p>', unsafe_allow_html=True)

    community_identity = st.multiselect(
        "I am a... *  (select all that apply)",
        ["Snowflake Data Superhero", "Streamlit Creator", "Both"],
        placeholder="Select your community identity",
    )

    years_snowflake = st.select_slider(
            "Years working with Snowflake",
            options=["< 6 months", "6–12 months", "1–2 years", "2–4 years", "4+ years"],
            value="1–2 years",
        )

    st.divider()

    # ── Section 3: The Conference ──────────────────────────────────────────────
    st.markdown('<span class="step-label">Section 3 of 4</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">The Conference</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us about the event you\'re planning to speak at.</p>', unsafe_allow_html=True)

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

    # ── Section 4: Talk & Support Request ────────────────────────────────────
    st.markdown('<span class="step-label">Section 4 of 4</span>', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Talk & Support Request</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Tell us what you may be presenting and what kind of support would help most.</p>', unsafe_allow_html=True)

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

    st.markdown("")

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
                "github_username": "",
                "twitter_handle": "",
                "website_url": "",
                "community_identity": ", ".join(community_identity),
                "superhero_profile_url": "",
                "streamlit_creator_profile_url": "",
                "snowflake_community_username": "",
                "years_snowflake": years_snowflake,
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
                ok = save_submission(payload)

            if ok:
                st.session_state.submitted = True
                st.rerun()
            else:
                st.warning(
                    "Could not save your submission. Please try again or contact the program team directly."
                )
