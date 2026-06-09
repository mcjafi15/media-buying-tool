# pages/01_New_Deal.py
import streamlit as st
from core.db import create_deal

st.set_page_config(page_title="New Deal", layout="wide")
st.title("New Deal")

with st.form("new_deal_form"):
    name = st.text_input("Deal Name *", placeholder="Acme Manufacturing Liquidation")
    col1, col2 = st.columns(2)
    with col1:
        deal_type = st.selectbox("Deal Type *", ["industrial", "real_estate", "retail", "other"])
        location = st.text_input("Location *", placeholder="Chicago, IL")
        total_budget = st.number_input("Total Media Budget ($) *", min_value=0.0, step=500.0)
    with col2:
        target_audience = st.text_area("Target Audience", placeholder="Manufacturing executives, equipment buyers...")
        start_date = st.date_input("Campaign Start Date")
        end_date = st.date_input("Campaign End Date")

    submitted = st.form_submit_button("Create Deal", type="primary")

if submitted:
    if not name or not location or total_budget <= 0:
        st.error("Deal Name, Location, and Budget are required.")
    elif end_date <= start_date:
        st.error("End date must be after start date.")
    else:
        deal_id = create_deal(
            name=name,
            type_=deal_type,
            location=location,
            target_audience=target_audience,
            total_budget=total_budget,
            start_date=str(start_date),
            end_date=str(end_date),
        )
        st.success(f"Deal '{name}' created (ID: {deal_id}). Go to **Media Plan** to generate your plan.")
        st.session_state["selected_deal_id"] = deal_id
