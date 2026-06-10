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
    mock_client.get_service.return_value.search.return_value = [mock_row]

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

    mock_client.get_service.return_value.search.return_value = [row_match, row_no_match]

    with patch("core.google_ads._get_client", return_value=mock_client):
        from core.google_ads import fetch_campaign_performance
        results = fetch_campaign_performance(customer_id="123", deal_name="Test Deal")

    assert len(results) == 1
    assert results[0]["impressions"] == 5000


def test_get_aggregated_metrics_empty_returns_zeros():
    with patch("core.google_ads._get_client") as mock_get_client:
        mock_get_client.return_value.get_service.return_value.search.return_value = []
        from core.google_ads import get_aggregated_metrics
        result = get_aggregated_metrics("123", "Nonexistent Deal")
    assert result == {"impressions": 0, "clicks": 0, "spend": 0.0, "conversions": 0}


def test_get_aggregated_metrics_sums_all_rows():
    mock_row1 = MagicMock()
    mock_row1.campaign.name = "Test Deal — Search"
    mock_row1.metrics.impressions = 5000
    mock_row1.metrics.clicks = 200
    mock_row1.metrics.cost_micros = 2000000000
    mock_row1.metrics.conversions = 5.0

    mock_row2 = MagicMock()
    mock_row2.campaign.name = "Test Deal — Display"
    mock_row2.metrics.impressions = 3000
    mock_row2.metrics.clicks = 100
    mock_row2.metrics.cost_micros = 1000000000
    mock_row2.metrics.conversions = 3.0

    with patch("core.google_ads._get_client") as mock_get_client:
        mock_get_client.return_value.get_service.return_value.search.return_value = [mock_row1, mock_row2]
        from core.google_ads import get_aggregated_metrics
        result = get_aggregated_metrics("123", "Test Deal")

    assert result["impressions"] == 8000
    assert result["clicks"] == 300
    assert abs(result["spend"] - 3000.0) < 0.01
    assert result["conversions"] == 8
