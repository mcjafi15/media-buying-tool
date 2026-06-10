# core/meta_ads.py
import os
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

_account_instance = None


def _get_account(ad_account_id: str):
    global _account_instance
    if _account_instance is None:
        FacebookAdsApi.init(
            app_id=os.environ["META_APP_ID"],
            app_secret=os.environ["META_APP_SECRET"],
            access_token=os.environ["META_ACCESS_TOKEN"],
        )
        _account_instance = AdAccount(ad_account_id)
    return _account_instance


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
    rows = fetch_meta_performance(ad_account_id, deal_name)
    return {
        "impressions": sum(r["impressions"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
        "spend": sum(r["spend"] for r in rows),
        "conversions": sum(r["conversions"] for r in rows),
    }
