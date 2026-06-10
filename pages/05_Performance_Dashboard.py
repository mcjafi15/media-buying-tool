# pages/05_Performance_Dashboard.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from core.db import (
    get_all_deals, get_placements, save_performance_snapshot,
    get_latest_snapshots, get_performance_snapshots,
)
from core.exporters import generate_performance_report

st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("Performance Dashboard")

deals = get_all_deals()
if not deals:
    st.info("No deals yet.")
    st.stop()

deal_options = {d["name"]: d for d in deals}
selected_name = st.selectbox("Select Deal", list(deal_options.keys()))
deal = deal_options[selected_name]
deal_id = deal["id"]

col_refresh, col_export = st.columns([1, 1])

with col_refresh:
    if st.button("🔄 Refresh Data from Ad Platforms"):
        errors = []
        try:
            from core.google_ads import get_aggregated_metrics as google_metrics
            g = google_metrics(os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""), deal["name"])
            save_performance_snapshot(deal_id, "google", g["impressions"], g["clicks"], g["spend"], g["conversions"])
        except Exception as e:
            errors.append(f"Google Ads: {e}")

        try:
            from core.meta_ads import get_aggregated_metrics as meta_metrics
            m = meta_metrics(os.environ.get("META_AD_ACCOUNT_ID", ""), deal["name"])
            save_performance_snapshot(deal_id, "meta", m["impressions"], m["clicks"], m["spend"], m["conversions"])
        except Exception as e:
            errors.append(f"Meta: {e}")

        try:
            from core.linkedin_ads import get_aggregated_metrics as li_metrics
            l = li_metrics(os.environ.get("LINKEDIN_AD_ACCOUNT_ID", ""), deal["name"])
            save_performance_snapshot(deal_id, "linkedin", l["impressions"], l["clicks"], l["spend"], l["conversions"])
        except Exception as e:
            errors.append(f"LinkedIn: {e}")

        if errors:
            for err in errors:
                st.warning(f"Could not sync: {err}")
        else:
            st.success("Data refreshed.")
        st.rerun()

snapshots = get_latest_snapshots(deal_id)
placements = get_placements(deal_id)
manual = [p for p in placements if not p["is_digital"]]

if not snapshots and not manual:
    st.info("No performance data yet. Add placements in Campaign Tracker or click Refresh Data.")
    st.stop()

total_digital_spend = sum(s["spend"] for s in snapshots)
total_impressions = sum(s["impressions"] for s in snapshots)
total_clicks = sum(s["clicks"] for s in snapshots)
total_conversions = sum(s["conversions"] for s in snapshots)
manual_spend = sum(p["actual_spend"] for p in manual)
total_spend = total_digital_spend + manual_spend
budget = deal["total_budget"]
cpm = (total_digital_spend / total_impressions * 1000) if total_impressions else 0
cpc = (total_digital_spend / total_clicks) if total_clicks else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Spend", f"${total_spend:,.0f}", f"of ${budget:,.0f}")
c2.metric("Budget Remaining", f"${budget - total_spend:,.0f}")
c3.metric("Impressions", f"{total_impressions:,}")
c4.metric("Clicks", f"{total_clicks:,}")
c5.metric("Conversions", str(total_conversions))

st.divider()

if snapshots:
    col_bar, col_tbl = st.columns([1, 1])
    with col_bar:
        df_snap = pd.DataFrame(snapshots)
        fig = px.bar(df_snap, x="platform", y="spend", title="Spend by Platform",
                     color="platform", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    with col_tbl:
        st.subheader("Platform Breakdown")
        display = df_snap[["platform", "impressions", "clicks", "spend", "conversions", "synced_at"]].copy()
        display.columns = ["Platform", "Impressions", "Clicks", "Spend ($)", "Conversions", "Last Sync"]
        st.dataframe(display, hide_index=True, use_container_width=True)

if manual:
    st.subheader("Print & OOH Placements")
    df_manual = pd.DataFrame(manual)[["vendor_name", "channel", "contracted_cost", "actual_spend", "status"]]
    df_manual.columns = ["Vendor", "Channel", "Contracted", "Actual Spend", "Status"]
    st.dataframe(df_manual, hide_index=True, use_container_width=True)

all_snaps = get_performance_snapshots(deal_id)
with col_export:
    if all_snaps or manual:
        try:
            st.download_button(
                "📥 Export Performance Report (PDF)",
                data=generate_performance_report(deal, snapshots, placements),
                file_name=f"{deal['name']}_performance_report.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"PDF report unavailable: {e}")
