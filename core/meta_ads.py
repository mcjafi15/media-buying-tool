# core/meta_ads.py
import os
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

_account_cache: dict = {}


def _get_account(ad_account_id: str) -> AdAccount:
    if ad_account_id not in _account_cache:
        FacebookAdsApi.init(
            app_id=os.environ["META_APP_ID"],
            app_secret=os.environ["META_APP_SECRET"],
            access_token=os.environ["META_ACCESS_TOKEN"],
        )
        _account_cache[ad_account_id] = AdAccount(ad_account_id)
    return _account_cache[ad_account_id]


def fetch_meta_performance(ad_account_id: str, deal_name: str) -> list[dict]:
    """Returns performance for all campaigns whose name contains deal_name."""
    account = _get_account(ad_account_id)
    campaigns = account.get_campaigns(fields=["name"])
    results = []
    for campaign in campaigns:
        if deal_name.lower() not in campaign["name"].lower():
            continue
        insights = campaign.get_insights(params={
            "fields": ["spend", "impressions", "clicks", "actions"],
            "date_preset": "maximum",
        })
        # insights.data is the first page only (~25 rows per campaign).
        # Sufficient for this use case — one aggregate row per campaign per request.
        for row in insights.data:
            conversions = sum(
                round(float(a.get("value", 0)))
                for a in row.get("actions", [])
                if a.get("action_type") in ("lead", "purchase", "complete_registration")
            )
            results.append({
                "campaign_name": campaign["name"],
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "spend": float(row.get("spend", 0)),
                "conversions": conversions,
            })
    return results


def get_aggregated_metrics(ad_account_id: str, deal_name: str) -> dict:
    """Returns totals across all matching campaigns for the given deal."""
    rows = fetch_meta_performance(ad_account_id, deal_name)
    return {
        "impressions": sum(r["impressions"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
        "spend": sum(r["spend"] for r in rows),
        "conversions": sum(r["conversions"] for r in rows),
    }
