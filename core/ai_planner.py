import json
import os
import anthropic

_client_instance = None


def _get_client():
    global _client_instance
    if _client_instance is None:
        _client_instance = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client_instance


def generate_media_plan(deal: dict) -> dict:
    """Calls Claude to generate a structured media plan for a deal. Returns a dict."""
    budget = deal["total_budget"]
    prompt = f"""You are an expert media buyer for deal marketing campaigns (auctions, liquidations, asset sales).

Generate a media plan for this deal:
- Deal Name: {deal["name"]}
- Deal Type: {deal["type"]}
- Location: {deal["location"]}
- Target Audience: {deal.get("target_audience", "General business buyers")}
- Total Media Budget: ${budget:,.0f}
- Campaign Start: {deal["start_date"]}
- Campaign End: {deal["end_date"]}

Available channels: Google Search, Google Display, Meta (Facebook/Instagram), LinkedIn, Print (trade pubs/newspapers), OOH (billboards/signage)
NOT available: TV, Radio

Return ONLY valid JSON — no markdown, no explanation — matching this exact structure:
{{
  "channel_mix": {{
    "digital": {{
      "pct": <int 0-100>,
      "usd": <float>,
      "breakdown": {{
        "google_search": <int pct of digital>,
        "google_display": <int pct of digital>,
        "meta": <int pct of digital>,
        "linkedin": <int pct of digital>
      }}
    }},
    "print": {{"pct": <int>, "usd": <float>, "notes": "<publication types>"}},
    "ooh": {{"pct": <int>, "usd": <float>, "notes": "<placement guidance>"}}
  }},
  "rationale": "<2-3 sentences>",
  "flight_schedule": "<timing strategy>",
  "targeting_notes": "<audience and targeting approach>",
  "keywords": ["<kw1>", "<kw2>"]
}}

Rules: channel pct values must sum to 100. digital breakdown pct values must sum to 100."""

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)
