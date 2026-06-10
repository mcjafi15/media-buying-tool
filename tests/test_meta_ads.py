# tests/test_meta_ads.py
import pytest
from unittest.mock import MagicMock, patch


def test_fetch_meta_performance_returns_list():
    mock_account = MagicMock()
    mock_campaign = MagicMock()
    mock_campaign.__getitem__ = lambda self, k: {"name": "Test Deal — Meta"}[k]
    mock_campaign.get_insights.return_value = MagicMock(data=[{
        "spend": "3000.00",
        "impressions": "80000",
        "clicks": "400",
        "actions": [{"action_type": "link_click", "value": "400"}],
    }])
    mock_account.get_campaigns.return_value = [mock_campaign]

    with patch("core.meta_ads._get_account", return_value=mock_account):
        from core.meta_ads import fetch_meta_performance
        results = fetch_meta_performance(ad_account_id="act_123", deal_name="Test Deal")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["impressions"] == 80000
    assert results[0]["spend"] == 3000.0


def test_fetch_meta_performance_filters_by_deal_name():
    mock_account = MagicMock()

    mock_match = MagicMock()
    mock_match.__getitem__ = lambda self, k: {"name": "Test Deal — Meta"}[k]
    mock_match.get_insights.return_value = MagicMock(data=[{
        "spend": "2000.00", "impressions": "50000", "clicks": "250", "actions": [],
    }])

    mock_no_match = MagicMock()
    mock_no_match.__getitem__ = lambda self, k: {"name": "Other Deal — Meta"}[k]
    mock_no_match.get_insights.return_value = MagicMock(data=[{
        "spend": "1000.00", "impressions": "30000", "clicks": "100", "actions": [],
    }])

    mock_account.get_campaigns.return_value = [mock_match, mock_no_match]

    with patch("core.meta_ads._get_account", return_value=mock_account):
        from core.meta_ads import fetch_meta_performance
        results = fetch_meta_performance(ad_account_id="act_123", deal_name="Test Deal")

    assert len(results) == 1
    assert results[0]["impressions"] == 50000


def test_get_aggregated_metrics_empty_returns_zeros():
    mock_account = MagicMock()
    mock_account.get_campaigns.return_value = []

    with patch("core.meta_ads._get_account", return_value=mock_account):
        from core.meta_ads import get_aggregated_metrics
        result = get_aggregated_metrics(ad_account_id="act_123", deal_name="Nonexistent")

    assert result == {"impressions": 0, "clicks": 0, "spend": 0.0, "conversions": 0}


def test_get_aggregated_metrics_sums_rows():
    mock_account = MagicMock()

    def make_campaign(name, spend, impressions, clicks):
        c = MagicMock()
        c.__getitem__ = lambda self, k: {"name": name}[k]
        c.get_insights.return_value = MagicMock(data=[{
            "spend": str(spend), "impressions": str(impressions),
            "clicks": str(clicks), "actions": [],
        }])
        return c

    mock_account.get_campaigns.return_value = [
        make_campaign("Test Deal — Search", "1500.00", "40000", "200"),
        make_campaign("Test Deal — Display", "800.00", "20000", "80"),
    ]

    with patch("core.meta_ads._get_account", return_value=mock_account):
        from core.meta_ads import get_aggregated_metrics
        result = get_aggregated_metrics(ad_account_id="act_123", deal_name="Test Deal")

    assert result["impressions"] == 60000
    assert result["clicks"] == 280
    assert abs(result["spend"] - 2300.0) < 0.01
