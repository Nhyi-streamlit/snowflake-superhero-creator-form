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

Submissions are saved to `MARKETING.PLAYGROUND.SUPERHERO_CREATOR_CONF_SUBMISSIONS` in Snowflake.

## Deploying to HuggingFace Spaces

Set the following **Repository Secrets** in Space Settings → Repository secrets:

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PASSWORD` | Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | Warehouse to use (default: `MARKETING_ADHOC`) |
| `SNOWFLAKE_ROLE` | Role to use (default: `MARKETING_SENSITIVE_RO`) |

## Local development

```bash
pip install -r requirements.txt
# Create .streamlit/secrets.toml with your Snowflake connection details
streamlit run streamlit_app.py
```

`.streamlit/secrets.toml` format:
```toml
[connections.snowflake]
account = "your-account"
user = "your-user"
password = "your-password"
warehouse = "MARKETING_ADHOC"
database = "MARKETING"
schema = "PLAYGROUND"
role = "MARKETING_SENSITIVE_RO"
```
