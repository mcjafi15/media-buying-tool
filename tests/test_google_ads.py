# tests/test_google_ads.py
import pytest
from unittest.mock import MagicMock, patch


def test_fetch_campaign_performance_returns_list():
    mock_client = MagicMock()
    mock_row = MagicMock()
    mock_row.campaign.name = "Test Deal — Google Search"
    mock_row.metrics.impressions = 10000
    mock_row.metrics.clicks = 500
    mock_row.metrics.cost_micros = 4500000000  # $4,500 in micros
    mock_row.metrics.conversions = 12.0
    mock_client.search.return_value = [mock_row]

    with patch("core.google_ads._get_client", return_value=mock_client):
        from core.google_ads import fetch_campaign_performance
        results = fetch_campaign_performance(customer_id="1234567890", deal_name="Test Deal")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["impressions"] == 10000
    assert results[0]["clicks"] == 500
    assert abs(results[0]["spend"] - 4500.0) < 0.01
    assert results[0]["conversions"] == 12


def test_fetch_campaign_performance_filters_by_deal_name():
    mock_client = MagicMock()
    row_match = MagicMock()
    row_match.campaign.name = "Test Deal — Search"
    row_match.metrics.impressions = 5000
    row_match.metrics.clicks = 200
    row_match.metrics.cost_micros = 2000000000
    row_match.metrics.conversions = 5.0

    row_no_match = MagicMock()
    row_no_match.campaign.name = "Other Deal — Search"
    row_no_match.metrics.impressions = 3000
    row_no_match.metrics.clicks = 100
    row_no_match.metrics.cost_micros = 1000000000
    row_no_match.metrics.conversions = 2.0

    mock_client.search.return_value = [row_match, row_no_match]

    with patch("core.google_ads._get_client", return_value=mock_client):
        from core.google_ads import fetch_campaign_performance
        results = fetch_campaign_performance(customer_id="123", deal_name="Test Deal")

    assert len(results) == 1
    assert results[0]["impressions"] == 5000
