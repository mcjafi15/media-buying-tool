import json
import os
import anthropic

_client_instance = None


def _get_client():
    global _client_instance
    if _client_instance is None:
        _client_instance = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client_instance


def generate_creative_ideas(deal: dict, plan: dict) -> dict:
    """Calls Claude to generate structured creative ideas for each channel in the media plan.

    Args:
        deal: Deal dict with name, type, location, target_audience, total_budget,
              start_date, end_date.
        plan: Approved media plan dict with channel_mix, rationale, flight_schedule,
              targeting_notes, keywords.

    Returns:
        Dict with creative ideas keyed by channel: google_search, meta, linkedin,
        print, ooh.
    """
    required = ("name", "type", "location", "total_budget", "start_date", "end_date")
    missing = [f for f in required if f not in deal]
    if missing:
        raise ValueError(f"Deal is missing required fields: {missing}")

    channel_mix = plan.get("channel_mix", {})
    digital = channel_mix.get("digital", {})
    digital_breakdown = digital.get("breakdown", {})
    print_channel = channel_mix.get("print", {})
    ooh_channel = channel_mix.get("ooh", {})

    channel_context_lines = []
    if digital:
        pct = digital.get("pct", 0)
        usd = digital.get("usd", 0)
        channel_context_lines.append(f"  - Digital: {pct}% (${usd:,.0f})")
        if digital_breakdown:
            gs_pct = digital_breakdown.get("google_search", 0)
            gd_pct = digital_breakdown.get("google_display", 0)
            meta_pct = digital_breakdown.get("meta", 0)
            li_pct = digital_breakdown.get("linkedin", 0)
            channel_context_lines.append(
                f"    * Google Search: {gs_pct}% of digital, "
                f"Google Display: {gd_pct}% of digital, "
                f"Meta: {meta_pct}% of digital, "
                f"LinkedIn: {li_pct}% of digital"
            )
    if print_channel:
        pct = print_channel.get("pct", 0)
        usd = print_channel.get("usd", 0)
        notes = print_channel.get("notes", "")
        channel_context_lines.append(f"  - Print: {pct}% (${usd:,.0f}) — {notes}")
    if ooh_channel:
        pct = ooh_channel.get("pct", 0)
        usd = ooh_channel.get("usd", 0)
        notes = ooh_channel.get("notes", "")
        channel_context_lines.append(f"  - OOH: {pct}% (${usd:,.0f}) — {notes}")

    channel_context = "\n".join(channel_context_lines)

    budget = deal["total_budget"]
    prompt = f"""You are an expert copywriter and creative strategist for Hilco Global, \
specializing in deal marketing campaigns (auctions, liquidations, asset sales).

Generate creative ad copy for the following deal across all active channels:
- Deal Name: {deal["name"]}
- Deal Type: {deal["type"]}
- Location: {deal["location"]}
- Target Audience: {deal.get("target_audience", "General business buyers")}
- Total Media Budget: ${budget:,.0f}
- Campaign Start: {deal["start_date"]}
- Campaign End: {deal["end_date"]}

Approved channel mix:
{channel_context}

Additional context:
- Flight schedule: {plan.get("flight_schedule", "")}
- Targeting notes: {plan.get("targeting_notes", "")}
- Keywords: {", ".join(plan.get("keywords", []))}

IMPORTANT PLATFORM CONSTRAINTS:
- Google Search (RSA): headlines must be 30 characters max; descriptions must be 90 characters max
- OOH (billboards): headlines must be 5-7 words max — short, punchy, readable at highway speed

Return ONLY valid JSON — no markdown, no explanation — matching this exact structure:
{{
  "google_search": {{
    "headlines": ["headline 1", "headline 2", ..., "headline 15"],
    "descriptions": ["desc 1", "desc 2", "desc 3", "desc 4"],
    "notes": "targeting and keyword guidance"
  }},
  "meta": {{
    "primary_text": ["option 1", "option 2", "option 3"],
    "headlines": ["headline 1", "headline 2", "headline 3"],
    "cta": "Learn More",
    "notes": "audience and format guidance"
  }},
  "linkedin": {{
    "headline": ["option 1", "option 2", "option 3"],
    "body": ["option 1", "option 2"],
    "notes": "targeting guidance"
  }},
  "print": {{
    "headlines": ["option 1", "option 2", "option 3"],
    "body_short": "short body copy (25-30 words)",
    "body_long": "long body copy (50-75 words)",
    "cta": "call to action text",
    "notes": "publication and format guidance"
  }},
  "ooh": {{
    "headlines": ["5-7 word option 1", "5-7 word option 2", "5-7 word option 3"],
    "subheads": ["subhead 1", "subhead 2"],
    "cta": "short cta",
    "notes": "placement and format guidance"
  }}
}}

Rules:
- google_search.headlines: exactly 15 items, each 30 characters or fewer
- google_search.descriptions: exactly 4 items, each 90 characters or fewer
- ooh.headlines: exactly 3 items, each 5-7 words maximum
- All copy must reflect the deal marketing context (auction, liquidation, asset sale) for Hilco Global"""

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}\nRaw response: {raw[:500]}") from exc
