# core/google_ads.py
import os
from google.ads.googleads.client import GoogleAdsClient


def _get_client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "use_proto_plus": True,
    })


def fetch_campaign_performance(customer_id: str, deal_name: str) -> list[dict]:
    """Returns aggregated performance for all campaigns whose name contains deal_name."""
    client = _get_client()

    query = """
        SELECT
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING ALL_TIME
        AND campaign.status = 'ENABLED'
    """

    response = client.search(customer_id=customer_id, query=query)

    results = []
    for row in response:
        if deal_name.lower() not in row.campaign.name.lower():
            continue
        results.append({
            "campaign_name": row.campaign.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "spend": row.metrics.cost_micros / 1_000_000,
            "conversions": int(row.metrics.conversions),
        })
    return results


def get_aggregated_metrics(customer_id: str, deal_name: str) -> dict:
    """Returns totals across all matching campaigns."""
    rows = fetch_campaign_performance(customer_id, deal_name)
    return {
        "impressions": sum(r["impressions"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
        "spend": sum(r["spend"] for r in rows),
        "conversions": sum(r["conversions"] for r in rows),
    }
