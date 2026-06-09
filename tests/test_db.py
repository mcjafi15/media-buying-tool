import pytest
import json
from core.db import (
    init_db, create_deal, get_deal, get_all_deals, update_deal_status,
    create_media_plan, get_media_plans, approve_media_plan, get_approved_plan,
    create_placement, get_placements, update_placement, delete_placement,
    save_performance_snapshot, get_performance_snapshots, get_latest_snapshots,
)

DEAL_KWARGS = dict(
    name="Test Deal",
    type_="industrial",
    location="Chicago, IL",
    target_audience="Manufacturing execs",
    total_budget=25000.0,
    start_date="2026-07-01",
    end_date="2026-08-15",
)


def test_init_db_creates_tables(tmp_db):
    import sqlite3
    conn = sqlite3.connect(str(tmp_db))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert {"deals", "media_plans", "placements", "performance_snapshots"} <= tables


def test_create_and_get_deal(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    deal = get_deal(deal_id)
    assert deal["name"] == "Test Deal"
    assert deal["total_budget"] == 25000.0
    assert deal["status"] == "draft"


def test_get_all_deals_returns_list(tmp_db):
    create_deal(**DEAL_KWARGS)
    create_deal(**{**DEAL_KWARGS, "name": "Second Deal"})
    deals = get_all_deals()
    assert len(deals) == 2


def test_update_deal_status(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    update_deal_status(deal_id, "active")
    assert get_deal(deal_id)["status"] == "active"


def test_create_and_approve_media_plan(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    plan_data = json.dumps({"channel_mix": {}, "rationale": "test"})
    plan_id = create_media_plan(deal_id, plan_data)
    assert get_approved_plan(deal_id) is None
    approve_media_plan(plan_id)
    approved = get_approved_plan(deal_id)
    assert approved is not None
    assert approved["id"] == plan_id


def test_media_plan_version_increments(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    create_media_plan(deal_id, "{}")
    create_media_plan(deal_id, "{}")
    plans = get_media_plans(deal_id)
    versions = {p["version"] for p in plans}
    assert versions == {1, 2}


def test_approve_unapproves_previous(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    id1 = create_media_plan(deal_id, "{}")
    id2 = create_media_plan(deal_id, "{}")
    approve_media_plan(id1)
    approve_media_plan(id2)
    plans = get_media_plans(deal_id)
    approved = [p for p in plans if p["approved"]]
    assert len(approved) == 1
    assert approved[0]["id"] == id2


def test_placement_crud(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    p_id = create_placement(deal_id, "Google", "google", "Search campaign", 5000.0,
                             "2026-07-01", "2026-08-15", is_digital=True)
    placements = get_placements(deal_id)
    assert len(placements) == 1
    assert placements[0]["vendor_name"] == "Google"
    assert placements[0]["is_digital"] == 1

    update_placement(p_id, actual_spend=4750.0, status="live")
    updated = get_placements(deal_id)[0]
    assert updated["actual_spend"] == 4750.0
    assert updated["status"] == "live"

    delete_placement(p_id)
    assert get_placements(deal_id) == []


def test_performance_snapshot(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    save_performance_snapshot(deal_id, "google", 10000, 500, 4500.0, 12)
    save_performance_snapshot(deal_id, "meta", 8000, 300, 3000.0, 8)
    snapshots = get_performance_snapshots(deal_id)
    assert len(snapshots) == 2


def test_get_latest_snapshots_one_per_platform(tmp_db):
    deal_id = create_deal(**DEAL_KWARGS)
    save_performance_snapshot(deal_id, "google", 5000, 200, 2000.0, 5)
    save_performance_snapshot(deal_id, "google", 10000, 500, 4500.0, 12)
    latest = get_latest_snapshots(deal_id)
    google_snaps = [s for s in latest if s["platform"] == "google"]
    assert len(google_snaps) == 1
    assert google_snaps[0]["impressions"] == 10000
