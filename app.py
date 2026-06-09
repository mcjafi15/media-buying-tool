# app.py
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from core.db import init_db

init_db()

st.set_page_config(page_title="Hilco Media Buying", page_icon="📊", layout="wide")

st.title("📊 Hilco Global — Media Buying Tool")
st.markdown("""
Welcome to the Hilco Media Buying Tool. Use the sidebar to navigate.

| Page | Purpose |
|---|---|
| New Deal | Create a new deal and define campaign parameters |
| Media Plan | Generate and approve an AI-powered media plan |
| Vendor Briefs | Download vendor brief and RFP documents |
| Campaign Tracker | Log and track media placements |
| Performance Dashboard | View live spend and results from ad platforms |
| Settings | Configure API credentials |
""")
