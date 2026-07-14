---
title: Snowflake Conference Support — Data Superheroes & Streamlit Creators
emoji: 🦸
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Conference support intake form for Snowflake Data Superheroes and Streamlit Creators
---

# Conference Support — Data Superheroes & Streamlit Creators

An intake form for recognized Snowflake **Data Superheroes** and **Streamlit Creators** who are attending a conference and want to explore what support Snowflake Developer Relations can offer.

## What it collects

- Contact info and social/community profiles
- Community identity (Data Superhero, Streamlit Creator, or both)
- Audience reach across platforms
- Past Snowflake content and open-source contributions
- Conference details (name, dates, location, format)
- Talk/session proposal and acceptance status
- Support requested (travel, hotel, ticket, coaching, amplification, etc.)

All submissions are written to a private Google Sheet for the DevRel team to review.

## Deploying

### HuggingFace Spaces (Docker)

Set the following **Repository Secrets** in Space Settings → Repository secrets:

| Secret | Description |
|--------|-------------|
| `GCP_SERVICE_ACCOUNT_JSON` | Full JSON contents of your GCP service account key file |
| `GOOGLE_SHEET_ID` | Spreadsheet ID from the Google Sheet URL |
| `GOOGLE_SHEET_WORKSHEET` | Tab name to write to (default: `Submissions`) |

The service account must have **Editor** access on the target spreadsheet.

Run `python setup_sheet.py` locally once to write the header row before going live.

### Local development

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# fill in credentials, then:
python setup_sheet.py        # write headers once
streamlit run streamlit_app.py
```
