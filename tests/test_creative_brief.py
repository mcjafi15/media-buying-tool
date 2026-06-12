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

SAMPLE_PLAN = {
    "channel_mix": {
        "digital": {
            "pct": 60,
            "usd": 15000.0,
            "breakdown": {
                "google_search": 40,
                "google_display": 20,
                "meta": 25,
                "linkedin": 15,
            },
        },
        "print": {"pct": 25, "usd": 6250.0, "notes": "Industry Week"},
        "ooh": {"pct": 15, "usd": 3750.0, "notes": "Billboards near facility"},
    },
    "rationale": "Strong B2B reach.",
    "flight_schedule": "Heavy first 2 weeks.",
    "targeting_notes": "Plant managers.",
    "keywords": ["equipment auction"],
}

VALID_RESPONSE = {
    "google_search": {
        "headlines": [
            "Acme Equipment Auction",
            "Industrial Liquidation Chicago",
            "Manufacturing Assets For Sale",
            "Bid On Acme Equipment",
            "Chicago Plant Liquidation",
            "Industrial Auction Event",
            "Buy Manufacturing Equipment",
            "Acme Liquidation Sale",
            "Equipment Auction Chicago IL",
            "Manufacturing Closeout Sale",
            "Industrial Assets Auction",
            "Plant Equipment For Sale",
            "Acme Factory Liquidation",
            "Bid On Factory Assets",
            "Chicago Equipment Auction",
        ],
        "descriptions": [
            "Bid on premium industrial equipment from Acme Manufacturing. Auction runs July-August 2026.",
            "Chicago-area liquidation sale featuring manufacturing assets. Register to bid today.",
            "Industrial equipment auction for plant managers and operations directors. View catalog now.",
            "Don't miss the Acme Manufacturing liquidation event in Chicago. Competitive bidding starts July 1.",
        ],
        "notes": "Target keywords: manufacturing equipment auction, industrial liquidation Chicago. Use broad match modifier for equipment categories.",
    },
    "meta": {
        "primary_text": [
            "Major industrial liquidation event coming to Chicago. Acme Manufacturing assets up for auction — register now to bid on premium equipment.",
            "Attention plant managers and operations directors: the Acme Manufacturing liquidation is your opportunity to acquire industrial equipment at auction prices.",
            "Chicago's biggest manufacturing liquidation of 2026. Equipment auction runs July 1 through August 15. Register today.",
        ],
        "headlines": [
            "Acme Manufacturing Auction",
            "Industrial Liquidation Chicago",
            "Bid on Factory Equipment",
        ],
        "cta": "Learn More",
        "notes": "Target manufacturing executives and plant managers in the Chicago metro area. Use carousel format to showcase equipment categories.",
    },
    "linkedin": {
        "headline": [
            "Acquire Industrial Assets at the Acme Manufacturing Liquidation",
            "Chicago Manufacturing Auction: Premium Equipment Now Available",
            "Acme Manufacturing Liquidation — Register to Bid Today",
        ],
        "body": [
            "Acme Manufacturing is liquidating its Chicago facility. This auction presents a rare opportunity for operations directors and plant managers to acquire quality industrial equipment. Bidding opens July 1, 2026.",
            "Seeking industrial equipment for your operations? The Acme Manufacturing liquidation auction in Chicago offers a wide range of assets. Event runs July 1 – August 15, 2026. Register now.",
        ],
        "notes": "Target by job title: Plant Manager, Operations Director, VP Manufacturing. Company size 50-500. Industry: Manufacturing.",
    },
    "print": {
        "headlines": [
            "Acme Manufacturing Liquidation Auction — Chicago, IL",
            "Industrial Equipment Auction: Acme Manufacturing Assets For Sale",
            "Don't Miss the Acme Manufacturing Liquidation This Summer",
        ],
        "body_short": "Premium industrial equipment from Acme Manufacturing now up for auction in Chicago. Bid on quality assets July 1–August 15, 2026. Register today.",
        "body_long": "Acme Manufacturing is conducting a complete liquidation of its Chicago facility, offering manufacturing executives and plant managers a rare opportunity to acquire premium industrial equipment at auction prices. From heavy machinery to precision tools, hundreds of lots will be available for competitive bidding. The auction runs July 1 through August 15, 2026. Preview the full catalog and register to bid at hilcoglobal.com.",
        "cta": "Register to Bid — hilcoglobal.com",
        "notes": "Run full-page in Industry Week. Half-page in Manufacturing Today. Lead with auction date and location in headline.",
    },
    "ooh": {
        "headlines": [
            "Acme Auction Chicago July 2026",
            "Industrial Liquidation Bid Now",
            "Manufacturing Assets For Sale Here",
        ],
        "subheads": [
            "Acme Manufacturing Liquidation — Register at hilcoglobal.com",
            "Industrial Equipment Auction • Chicago, IL • July 1–Aug 15",
        ],
        "cta": "hilcoglobal.com",
        "notes": "Place billboards within 5 miles of the Acme facility and near major industrial corridors. Bold headline, minimal copy. QR code optional.",
    },
}


def _mock_client(response_dict):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(response_dict))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_generate_creative_ideas_returns_dict():
    with patch("core.creative_brief._get_client", return_value=_mock_client(VALID_RESPONSE)):
        from core.creative_brief import generate_creative_ideas
        result = generate_creative_ideas(SAMPLE_DEAL, SAMPLE_PLAN)
    assert isinstance(result, dict)


def test_generate_creative_ideas_has_required_keys():
    with patch("core.creative_brief._get_client", return_value=_mock_client(VALID_RESPONSE)):
        from core.creative_brief import generate_creative_ideas
        result = generate_creative_ideas(SAMPLE_DEAL, SAMPLE_PLAN)
    for key in ("google_search", "meta", "linkedin", "print", "ooh"):
        assert key in result, f"Missing key: {key}"


def test_generate_creative_ideas_google_has_15_headlines():
    with patch("core.creative_brief._get_client", return_value=_mock_client(VALID_RESPONSE)):
        from core.creative_brief import generate_creative_ideas
        result = generate_creative_ideas(SAMPLE_DEAL, SAMPLE_PLAN)
    assert len(result["google_search"]["headlines"]) == 15


def test_generate_creative_ideas_calls_claude_with_deal_info():
    mock_client = _mock_client(VALID_RESPONSE)
    with patch("core.creative_brief._get_client", return_value=mock_client):
        from core.creative_brief import generate_creative_ideas
        generate_creative_ideas(SAMPLE_DEAL, SAMPLE_PLAN)
    call_kwargs = mock_client.messages.create.call_args
    prompt_text = call_kwargs[1]["messages"][0]["content"]
    assert "Acme Manufacturing Liquidation" in prompt_text
    assert "Chicago, IL" in prompt_text
