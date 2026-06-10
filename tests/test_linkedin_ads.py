# tests/test_linkedin_ads.py
import pytest
from unittest.mock import patch, MagicMock

MOCK_CAMPAIGNS_RESP = {
    "elements": [
        {"id": 111, "name": "Test Deal — LinkedIn", "status": "ACTIVE"},
        {"id": 222, "name": "Other Deal — LinkedIn", "status": "ACTIVE"},
    ]
}

MOCK_ANALYTICS_RESP = {
    "elements": [{
        "totalSpend": {"amount": "2500.00"},
        "impressions": 60000,
        "clicks": 300,
        "externalWebsiteConversions": 8,
    }]
}


def test_fetch_linkedin_performance_filters_by_deal():
    with patch("core.linkedin_ads._get") as mock_get:
        mock_get.side_effect = [
            MagicMock(json=lambda: MOCK_CAMPAIGNS_RESP),
            MagicMock(json=lambda: MOCK_ANALYTICS_RESP),
        ]
        from core.linkedin_ads import fetch_linkedin_performance
        results = fetch_linkedin_performance(ad_account_id="123", deal_name="Test Deal")

    assert len(results) == 1
    assert results[0]["impressions"] == 60000
    assert results[0]["spend"] == 2500.0
    assert results[0]["clicks"] == 300


def test_fetch_linkedin_performance_no_matching_campaigns():
    with patch("core.linkedin_ads._get") as mock_get:
        mock_get.return_value = MagicMock(json=lambda: {"elements": []})
        from core.linkedin_ads import fetch_linkedin_performance
        results = fetch_linkedin_performance(ad_account_id="123", deal_name="Nonexistent")

    assert results == []


def test_get_aggregated_metrics_empty_returns_zeros():
    with patch("core.linkedin_ads._get") as mock_get:
        mock_get.return_value = MagicMock(json=lambda: {"elements": []})
        from core.linkedin_ads import get_aggregated_metrics
        result = get_aggregated_metrics(ad_account_id="123", deal_name="Nonexistent")

    assert result == {"impressions": 0, "clicks": 0, "spend": 0.0, "conversions": 0}


def test_get_aggregated_metrics_sums_rows():
    campaigns_resp = {
        "elements": [
            {"id": 111, "name": "Test Deal — Search", "status": "ACTIVE"},
            {"id": 222, "name": "Test Deal — Display", "status": "ACTIVE"},
        ]
    }
    analytics_resp_1 = {
        "elements": [{
            "totalSpend": {"amount": "1500.00"},
            "impressions": 40000,
            "clicks": 200,
            "externalWebsiteConversions": 5,
        }]
    }
    analytics_resp_2 = {
        "elements": [{
            "totalSpend": {"amount": "800.00"},
            "impressions": 20000,
            "clicks": 80,
            "externalWebsiteConversions": 3,
        }]
    }

    with patch("core.linkedin_ads._get") as mock_get:
        mock_get.side_effect = [
            MagicMock(json=lambda: campaigns_resp),
            MagicMock(json=lambda: analytics_resp_1),
            MagicMock(json=lambda: analytics_resp_2),
        ]
        from core.linkedin_ads import get_aggregated_metrics
        result = get_aggregated_metrics(ad_account_id="123", deal_name="Test Deal")

    assert result["impressions"] == 60000
    assert result["clicks"] == 280
    assert abs(result["spend"] - 2300.0) < 0.01
    assert result["conversions"] == 8
