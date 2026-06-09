# pages/02_Media_Plan.py
import json
import streamlit as st
from core.db import get_all_deals, create_media_plan, get_media_plans, approve_media_plan, get_approved_plan
from core.ai_planner import generate_media_plan

st.set_page_config(page_title="Media Plan", layout="wide")
st.title("Media Plan")

deals = get_all_deals()
if not deals:
    st.info("No deals yet. Create one in **New Deal**.")
    st.stop()

deal_options = {f"{d['name']} (${d['total_budget']:,.0f})": d["id"] for d in deals}
selected_label = st.selectbox("Select Deal", list(deal_options.keys()))
deal_id = deal_options[selected_label]
deal = next(d for d in deals if d["id"] == deal_id)

st.markdown(f"**Type:** {deal['type']} | **Location:** {deal['location']} | "
            f"**Budget:** ${deal['total_budget']:,.0f} | **Dates:** {deal['start_date']} → {deal['end_date']}")

st.divider()

col_gen, col_hist = st.columns([3, 1])

with col_gen:
    if st.button("✨ Generate New Plan", type="primary"):
        with st.spinner("Generating media plan with Claude AI..."):
            try:
                plan_dict = generate_media_plan(deal)
                plan_id = create_media_plan(deal_id, json.dumps(plan_dict))
                st.success(f"Plan v{len(get_media_plans(deal_id))} generated.")
                st.rerun()
            except Exception as e:
                st.error(f"Generation failed: {e}")

plans = get_media_plans(deal_id)
approved = get_approved_plan(deal_id)

with col_hist:
    if plans:
        st.metric("Versions", len(plans))
        if approved:
            st.success("✅ Plan approved")

if not plans:
    st.info("No plans yet. Click **Generate New Plan**.")
    st.stop()

# Show most recent plan
selected_plan = plans[0]
plan_data = json.loads(selected_plan["plan_json"])

st.subheader(f"Plan v{selected_plan['version']}" + (" ✅ Approved" if selected_plan["approved"] else ""))

col1, col2, col3 = st.columns(3)
cm = plan_data["channel_mix"]
with col1:
    st.metric("Digital", f"${cm['digital']['usd']:,.0f}", f"{cm['digital']['pct']}%")
with col2:
    st.metric("Print", f"${cm['print']['usd']:,.0f}", f"{cm['print']['pct']}%")
with col3:
    st.metric("OOH", f"${cm['ooh']['usd']:,.0f}", f"{cm['ooh']['pct']}%")

with st.expander("Digital Breakdown"):
    for platform, pct in cm["digital"]["breakdown"].items():
        sub_usd = cm["digital"]["usd"] * pct / 100
        st.write(f"**{platform.replace('_', ' ').title()}:** {pct}% — ${sub_usd:,.0f}")

st.markdown(f"**Rationale:** {plan_data.get('rationale', '')}")
st.markdown(f"**Flight Schedule:** {plan_data.get('flight_schedule', '')}")
st.markdown(f"**Targeting Notes:** {plan_data.get('targeting_notes', '')}")
if plan_data.get("keywords"):
    st.markdown(f"**Keywords:** {', '.join(plan_data['keywords'])}")

if not selected_plan["approved"]:
    if st.button("✅ Approve This Plan", type="primary"):
        approve_media_plan(selected_plan["id"])
        st.success("Plan approved!")
        st.rerun()

if len(plans) > 1:
    with st.expander("Previous Versions"):
        for p in plans[1:]:
            st.write(f"v{p['version']} — {p['created_at']} {'✅' if p['approved'] else ''}")
