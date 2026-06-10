# pages/03_Vendor_Briefs.py
import json
import streamlit as st
from core.db import get_all_deals, get_approved_plan, get_deal
from core.exporters import (
    generate_digital_brief, generate_print_brief, generate_ooh_brief,
    generate_rfp_template, generate_budget_approval_form, generate_media_plan_summary,
)

st.set_page_config(page_title="Vendor Briefs", layout="wide")
st.title("Vendor Briefs & Documents")

deals = get_all_deals()
if not deals:
    st.info("No deals yet.")
    st.stop()

deal_options = {d["name"]: d["id"] for d in deals}
selected_name = st.selectbox("Select Deal", list(deal_options.keys()))
deal_id = deal_options[selected_name]
deal = get_deal(deal_id)
approved = get_approved_plan(deal_id)

if not approved:
    st.warning("No approved media plan for this deal. Go to **Media Plan** to generate and approve one.")
    st.stop()

plan = json.loads(approved["plan_json"])

st.success(f"Using approved Plan v{approved['version']}")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Vendor Briefs")
    try:
        st.download_button(
            "📥 Digital Brief (.docx)",
            data=generate_digital_brief(deal, plan),
            file_name=f"{deal['name']}_digital_brief.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Digital Brief unavailable: {e}")
    try:
        st.download_button(
            "📥 Print Brief (.docx)",
            data=generate_print_brief(deal, plan),
            file_name=f"{deal['name']}_print_brief.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Print Brief unavailable: {e}")
    try:
        st.download_button(
            "📥 OOH Brief (.docx)",
            data=generate_ooh_brief(deal, plan),
            file_name=f"{deal['name']}_ooh_brief.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"OOH Brief unavailable: {e}")

with col2:
    st.subheader("RFP Templates")
    try:
        st.download_button(
            "📥 Print RFP (.docx)",
            data=generate_rfp_template(deal, plan, "print"),
            file_name=f"{deal['name']}_print_rfp.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Print RFP unavailable: {e}")
    try:
        st.download_button(
            "📥 OOH RFP (.docx)",
            data=generate_rfp_template(deal, plan, "ooh"),
            file_name=f"{deal['name']}_ooh_rfp.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"OOH RFP unavailable: {e}")

with col3:
    st.subheader("Internal Documents")
    try:
        st.download_button(
            "📥 Media Plan Summary (.docx)",
            data=generate_media_plan_summary(deal, plan),
            file_name=f"{deal['name']}_media_plan.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Media Plan Summary unavailable: {e}")
    try:
        st.download_button(
            "📥 Budget Approval Form (.docx)",
            data=generate_budget_approval_form(deal, plan),
            file_name=f"{deal['name']}_budget_approval.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Budget Approval Form unavailable: {e}")
