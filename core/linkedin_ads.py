# core/linkedin_ads.py
import os
import requests

_API_BASE = "https://api.linkedin.com/v2"
_VERSION = "202406"


def _get(path: str, params: dict = None):
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": _VERSION,
    }
    return requests.get(f"{_API_BASE}{path}", headers=headers, params=params or {})


def _get_campaigns(ad_account_id: str) -> list[dict]:
    resp = _get("/adCampaignsV2", {
        "q": "search",
        "search.account.values[0]": f"urn:li:sponsoredAccount:{ad_account_id}",
    })
    resp.raise_for_status()
    return resp.json().get("elements", [])


def _get_analytics(campaign_id: int) -> dict:
    resp = _get("/adAnalyticsV2", {
        "q": "analytics",
        "pivot": "CAMPAIGN",
        "timeGranularity": "ALL",
        "campaigns[0]": f"urn:li:sponsoredCampaign:{campaign_id}",
        "fields": "totalSpend,impressions,clicks,externalWebsiteConversions",
    })
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    return elements[0] if elements else {}


def fetch_linkedin_performance(ad_account_id: str, deal_name: str) -> list[dict]:
    """Returns performance for all campaigns whose name contains deal_name."""
    campaigns = _get_campaigns(ad_account_id)
    results = []
    for campaign in campaigns:
        if deal_name.lower() not in campaign.get("name", "").lower():
            continue
        analytics = _get_analytics(campaign["id"])
        results.append({
            "campaign_name": campaign["name"],
            "impressions": analytics.get("impressions", 0),
            "clicks": analytics.get("clicks", 0),
            "spend": float(analytics.get("totalSpend", {}).get("amount", 0)),
            "conversions": analytics.get("externalWebsiteConversions", 0),
        })
    return results


def get_aggregated_metrics(ad_account_id: str, deal_name: str) -> dict:
    """Returns totals across all matching campaigns for the given deal."""
    rows = fetch_linkedin_performance(ad_account_id, deal_name)
    return {
        "impressions": sum(r["impressions"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
        "spend": sum(r["spend"] for r in rows),
        "conversions": sum(r["conversions"] for r in rows),
    }
