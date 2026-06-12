# pages/07_Creative_Brief.py
import json
import streamlit as st
from core.db import get_all_deals, get_approved_plan, get_deal
from core.creative_brief import generate_creative_ideas
from core.exporters import generate_creative_brief_doc

st.set_page_config(page_title="Creative Brief", layout="wide")
st.title("Creative Brief")

deals = get_all_deals()
if not deals:
    st.info("No deals yet. Create one in **New Deal**.")
    st.stop()

deal_options = {d["name"]: d["id"] for d in deals}
selected_name = st.selectbox("Select Deal", list(deal_options.keys()))
deal_id = deal_options[selected_name]
deal = get_deal(deal_id)
approved = get_approved_plan(deal_id)

if not approved:
    st.warning("No approved media plan for this deal. Go to **Media Plan** to generate and approve one first.")
    st.stop()

plan = json.loads(approved["plan_json"])

st.markdown(
    f"**Deal:** {deal['name']} | **Type:** {deal['type']} | "
    f"**Location:** {deal['location']} | **Budget:** ${deal['total_budget']:,.0f}"
)
st.divider()

if st.button("✨ Generate Creative Ideas", type="primary"):
    with st.spinner("Generating creative ideas with Claude AI..."):
        try:
            creative = generate_creative_ideas(deal, plan)
            st.session_state["creative"] = creative
            st.session_state["creative_deal_id"] = deal_id
            st.session_state.pop("creative_doc_bytes", None)
        except Exception as e:
            st.error(f"Generation failed: {e}")

# Fix 4: Clear stale cached bytes on deal change
if st.session_state.get("creative_deal_id") != deal_id:
    st.session_state.pop("creative_doc_bytes", None)

creative = st.session_state.get("creative") if st.session_state.get("creative_deal_id") == deal_id else None

if not creative:
    st.info("Click **Generate Creative Ideas** to create ad copy for all channels.")
    st.stop()

# Fix 3: Cache doc bytes in session state
doc_bytes = st.session_state.get("creative_doc_bytes")
if doc_bytes is None:
    try:
        doc_bytes = generate_creative_brief_doc(deal, plan, creative)
        st.session_state["creative_doc_bytes"] = doc_bytes
    except Exception as e:
        st.error(f"Could not generate document: {e}")
        doc_bytes = None

if doc_bytes:
    st.download_button(
        "📥 Download Creative Brief (.docx)",
        data=doc_bytes,
        file_name=f"{deal['name']}_creative_brief.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )

st.divider()

# Display creative ideas in tabs
tab_google, tab_meta, tab_li, tab_print, tab_ooh = st.tabs(
    ["Google Search", "Meta", "LinkedIn", "Print", "OOH"]
)

# Fix 6: Add empty tab guard to all 5 tabs
with tab_google:
    gs = creative.get("google_search", {})
    if not gs:
        st.info("No ideas generated for this channel.")
    else:
        st.subheader("Headlines (30 chars max)")
        for i, h in enumerate(gs.get("headlines", []), 1):
            st.write(f"{i}. {h}")
        st.subheader("Descriptions (90 chars max)")
        for i, d in enumerate(gs.get("descriptions", []), 1):
            st.write(f"{i}. {d}")
        if gs.get("notes"):
            st.info(gs["notes"])

with tab_meta:
    meta = creative.get("meta", {})
    if not meta:
        st.info("No ideas generated for this channel.")
    else:
        st.subheader("Primary Text Options")
        for i, t in enumerate(meta.get("primary_text", []), 1):
            st.write(f"{i}. {t}")
        st.subheader("Headlines")
        for i, h in enumerate(meta.get("headlines", []), 1):
            st.write(f"{i}. {h}")
        # Fix 5: Replace st.metric with st.markdown for CTA fields
        st.markdown(f"**Recommended CTA:** {meta.get('cta', '')}")
        if meta.get("notes"):
            st.info(meta["notes"])

with tab_li:
    li = creative.get("linkedin", {})
    if not li:
        st.info("No ideas generated for this channel.")
    else:
        st.subheader("Headline Options")
        for i, h in enumerate(li.get("headline", []), 1):
            st.write(f"{i}. {h}")
        st.subheader("Body Copy Options")
        for i, b in enumerate(li.get("body", []), 1):
            st.write(f"{i}. {b}")
        if li.get("notes"):
            st.info(li["notes"])

with tab_print:
    pr = creative.get("print", {})
    if not pr:
        st.info("No ideas generated for this channel.")
    else:
        st.subheader("Headline Options")
        for i, h in enumerate(pr.get("headlines", []), 1):
            st.write(f"{i}. {h}")
        st.subheader("Short Body Copy")
        st.write(pr.get("body_short", ""))
        st.subheader("Long Body Copy")
        st.write(pr.get("body_long", ""))
        # Fix 5: Replace st.metric with st.markdown for CTA fields
        st.markdown(f"**Call to Action:** {pr.get('cta', '')}")
        if pr.get("notes"):
            st.info(pr["notes"])

with tab_ooh:
    ooh = creative.get("ooh", {})
    if not ooh:
        st.info("No ideas generated for this channel.")
    else:
        st.subheader("Billboard Headlines (5-7 words)")
        for i, h in enumerate(ooh.get("headlines", []), 1):
            st.write(f"{i}. {h}")
        st.subheader("Subheadlines")
        for i, s in enumerate(ooh.get("subheads", []), 1):
            st.write(f"{i}. {s}")
        # Fix 5: Replace st.metric with st.markdown for CTA fields
        st.markdown(f"**Call to Action:** {ooh.get('cta', '')}")
        if ooh.get("notes"):
            st.info(ooh["notes"])
