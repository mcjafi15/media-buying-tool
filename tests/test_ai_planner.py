import json
import pytest
from unittest.mock import MagicMock, patch

SAMPLE_DEAL = {
    "name": "Acme Manufacturing Liquidation",
    "type": "industrial",
    "location": "Chicago, IL",
    "target_audience": "Manufacturing executives",
    "total_budget": 25000.0,
    "start_date": "2026-07-01",
    "end_date": "2026-08-15",
}

VALID_PLAN = {
    "channel_mix": {
        "digital": {
            "pct": 60, "usd": 15000.0,
            "breakdown": {"google_search": 40, "google_display": 20, "meta": 25, "linkedin": 15}
        },
        "print": {"pct": 25, "usd": 6250.0, "notes": "Industry Week, Manufacturing Today"},
        "ooh": {"pct": 15, "usd": 3750.0, "notes": "Billboards near facility"},
    },
    "rationale": "Industrial buyers research online; LinkedIn reaches B2B decision-makers.",
    "flight_schedule": "Heavy digital weeks 1-3, sustain through week 6",
    "targeting_notes": "Job titles: Plant Manager, Operations Director",
    "keywords": ["manufacturing equipment auction", "industrial liquidation Chicago"],
}


def _mock_client(plan_dict):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(plan_dict))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_generate_media_plan_returns_dict():
    with patch("core.ai_planner._get_client", return_value=_mock_client(VALID_PLAN)):
        from core.ai_planner import generate_media_plan
        result = generate_media_plan(SAMPLE_DEAL)
    assert isinstance(result, dict)


def test_generate_media_plan_has_required_keys():
    with patch("core.ai_planner._get_client", return_value=_mock_client(VALID_PLAN)):
        from core.ai_planner import generate_media_plan
        result = generate_media_plan(SAMPLE_DEAL)
    for key in ("channel_mix", "rationale", "flight_schedule", "targeting_notes", "keywords"):
        assert key in result, f"Missing key: {key}"


def test_generate_media_plan_channel_pcts_sum_to_100():
    with patch("core.ai_planner._get_client", return_value=_mock_client(VALID_PLAN)):
        from core.ai_planner import generate_media_plan
        result = generate_media_plan(SAMPLE_DEAL)
    total = sum(v["pct"] for v in result["channel_mix"].values())
    assert total == 100


def test_generate_media_plan_calls_claude_with_deal_info():
    mock_client = _mock_client(VALID_PLAN)
    with patch("core.ai_planner._get_client", return_value=mock_client):
        from core.ai_planner import generate_media_plan
        generate_media_plan(SAMPLE_DEAL)
    call_kwargs = mock_client.messages.create.call_args
    prompt_text = call_kwargs[1]["messages"][0]["content"]
    assert "Chicago, IL" in prompt_text
    assert "25,000" in prompt_text or "25000" in prompt_text
