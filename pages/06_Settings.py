# pages/06_Settings.py
import os
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Settings", layout="wide")
st.title("Settings — API Credentials")

st.info(
    "Credentials are stored in a `.env` file in the project root and loaded at startup. "
    "For Streamlit Cloud deployment, set these as Environment Variables in the Cloud dashboard instead."
)

ENV_PATH = Path(__file__).parent.parent / ".env"


def load_env_file():
    if not ENV_PATH.exists():
        return {}
    result = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


_MANAGED_KEYS = {
    "ANTHROPIC_API_KEY", "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID",
    "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN",
    "LINKEDIN_AD_ACCOUNT_ID",
}


def save_env_file(values: dict):
    import os as _os
    existing: dict = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update({k: v for k, v in values.items() if v})
    for key in _MANAGED_KEYS:
        if key not in values or not values[key]:
            existing.pop(key, None)
    lines = [f"{k}={v}" for k, v in existing.items()]
    content = "\n".join(lines) + "\n"
    tmp = ENV_PATH.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    _os.replace(tmp, ENV_PATH)


current = load_env_file()

with st.form("settings_form"):
    st.subheader("Anthropic (Claude AI)")
    anthropic_key = st.text_input("ANTHROPIC_API_KEY", value=current.get("ANTHROPIC_API_KEY", ""),
                                   type="password")

    st.subheader("Google Ads")
    g_dev_token = st.text_input("GOOGLE_ADS_DEVELOPER_TOKEN",
                                 value=current.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""), type="password")
    g_client_id = st.text_input("GOOGLE_ADS_CLIENT_ID", value=current.get("GOOGLE_ADS_CLIENT_ID", ""))
    g_client_secret = st.text_input("GOOGLE_ADS_CLIENT_SECRET",
                                     value=current.get("GOOGLE_ADS_CLIENT_SECRET", ""), type="password")
    g_refresh = st.text_input("GOOGLE_ADS_REFRESH_TOKEN",
                               value=current.get("GOOGLE_ADS_REFRESH_TOKEN", ""), type="password")
    g_customer = st.text_input("GOOGLE_ADS_LOGIN_CUSTOMER_ID",
                                value=current.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""))

    st.subheader("Meta (Facebook/Instagram)")
    meta_app_id = st.text_input("META_APP_ID", value=current.get("META_APP_ID", ""))
    meta_app_secret = st.text_input("META_APP_SECRET", value=current.get("META_APP_SECRET", ""),
                                     type="password")
    meta_token = st.text_input("META_ACCESS_TOKEN", value=current.get("META_ACCESS_TOKEN", ""),
                                type="password")
    meta_account = st.text_input("META_AD_ACCOUNT_ID", value=current.get("META_AD_ACCOUNT_ID", ""))

    st.subheader("LinkedIn")
    li_client_id = st.text_input("LINKEDIN_CLIENT_ID", value=current.get("LINKEDIN_CLIENT_ID", ""))
    li_client_secret = st.text_input("LINKEDIN_CLIENT_SECRET",
                                      value=current.get("LINKEDIN_CLIENT_SECRET", ""), type="password")
    li_token = st.text_input("LINKEDIN_ACCESS_TOKEN", value=current.get("LINKEDIN_ACCESS_TOKEN", ""),
                              type="password")
    li_account = st.text_input("LINKEDIN_AD_ACCOUNT_ID", value=current.get("LINKEDIN_AD_ACCOUNT_ID", ""))

    saved = st.form_submit_button("Save Credentials", type="primary")

if saved:
    try:
        save_env_file({
            "ANTHROPIC_API_KEY": anthropic_key,
            "GOOGLE_ADS_DEVELOPER_TOKEN": g_dev_token,
            "GOOGLE_ADS_CLIENT_ID": g_client_id,
            "GOOGLE_ADS_CLIENT_SECRET": g_client_secret,
            "GOOGLE_ADS_REFRESH_TOKEN": g_refresh,
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID": g_customer,
            "META_APP_ID": meta_app_id,
            "META_APP_SECRET": meta_app_secret,
            "META_ACCESS_TOKEN": meta_token,
            "META_AD_ACCOUNT_ID": meta_account,
            "LINKEDIN_CLIENT_ID": li_client_id,
            "LINKEDIN_CLIENT_SECRET": li_client_secret,
            "LINKEDIN_ACCESS_TOKEN": li_token,
            "LINKEDIN_AD_ACCOUNT_ID": li_account,
        })
        st.success("Saved to .env. Restart the app for new values to take effect.")
    except OSError as e:
        st.error(f"Could not write .env file: {e}")
