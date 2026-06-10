# pages/04_Campaign_Tracker.py
import streamlit as st
import pandas as pd
from core.db import (
    get_all_deals, get_placements, create_placement,
    update_placement, delete_placement,
)

st.set_page_config(page_title="Campaign Tracker", layout="wide")
st.title("Campaign Tracker")

deals = get_all_deals()
if not deals:
    st.info("No deals yet.")
    st.stop()

deal_options = {d["name"]: d["id"] for d in deals}
selected_name = st.selectbox("Select Deal", list(deal_options.keys()))
deal_id = deal_options[selected_name]

st.subheader("Add Placement")
with st.form("add_placement"):
    col1, col2 = st.columns(2)
    with col1:
        vendor = st.text_input("Vendor / Platform")
        channel = st.selectbox("Channel", ["google", "meta", "linkedin", "print", "ooh"])
        description = st.text_input("Description")
    with col2:
        contracted = st.number_input("Contracted Cost ($)", min_value=0.0, step=100.0)
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
    add_submitted = st.form_submit_button("Add Placement")

if add_submitted and vendor:
    if end <= start:
        st.error("End date must be after start date.")
    else:
        is_digital = channel in ("google", "meta", "linkedin")
        create_placement(deal_id, vendor, channel, description, contracted,
                         str(start), str(end), is_digital=is_digital)
        st.success(f"Added: {vendor} ({channel})")
        st.rerun()
elif add_submitted:
    st.error("Vendor / Platform is required.")

st.divider()
st.subheader("Placements")
placements = get_placements(deal_id)

if not placements:
    st.info("No placements yet. Add one above.")
    st.stop()

df = pd.DataFrame(placements)
display_cols = ["id", "vendor_name", "channel", "description",
                "contracted_cost", "actual_spend", "status", "start_date", "end_date"]
safe_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[safe_cols], use_container_width=True, hide_index=True)

total_contracted = df["contracted_cost"].sum()
total_actual = df["actual_spend"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Total Contracted", f"${total_contracted:,.0f}")
c2.metric("Total Actual Spend", f"${total_actual:,.0f}")
c3.metric("Remaining", f"${total_contracted - total_actual:,.0f}")

st.subheader("Edit / Delete Placement")
placement_labels = [f"{p['vendor_name']} — {p['channel']} (ID {p['id']})" for p in placements]
label_to_id = {f"{p['vendor_name']} — {p['channel']} (ID {p['id']})": p["id"] for p in placements}
selected_label = st.selectbox("Select placement to edit", placement_labels)
selected_id = label_to_id[selected_label]
selected = next(p for p in placements if p["id"] == selected_id)

with st.form("edit_placement"):
    new_actual = st.number_input("Actual Spend ($)", value=float(selected["actual_spend"]), step=100.0)
    _statuses = ["pending", "live", "complete"]
    _status_idx = _statuses.index(selected["status"]) if selected["status"] in _statuses else 0
    new_status = st.selectbox("Status", _statuses, index=_status_idx)
    col_save, col_del = st.columns(2)
    save = col_save.form_submit_button("Save Changes")
    delete = col_del.form_submit_button("Delete", type="secondary")

if save:
    update_placement(selected_id, actual_spend=new_actual, status=new_status)
    st.success("Updated.")
    st.rerun()
if delete:
    delete_placement(selected_id)
    st.success("Deleted.")
    st.rerun()
