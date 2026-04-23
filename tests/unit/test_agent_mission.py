"""Unit tests for agent mission JSON extraction and validation."""

import pytest

from yahboom_mcp.agent_mission import MissionPlanV1, extract_json_object


def test_extract_json_plain():
    raw = '{"version": 1, "intent": "search", "behavior": "room_search"}'
    d = extract_json_object(raw)
    assert d["intent"] == "search"


def test_extract_json_fenced():
    raw = '```json\n{"version": 1, "intent": "navigate"}\n```'
    d = extract_json_object(raw)
    assert d["intent"] == "navigate"


def test_extract_json_prefix_garbage():
    raw = 'Here you go:\n{"version": 1, "intent": "speak", "target_description": "hi"}\nThanks'
    d = extract_json_object(raw)
    assert d["intent"] == "speak"


def test_mission_plan_defaults():
    m = MissionPlanV1.model_validate({"intent": "search"})
    assert m.behavior == "idle"
    assert m.version == 1
    assert m.nav2_goal is None


def test_mission_plan_nav2_goal_coerced():
    m = MissionPlanV1.model_validate(
        {
            "behavior": "go_to_waypoint",
            "nav2_goal": {"frame_id": "map", "x": 1.0, "y": 2.0, "yaw_deg": 90.0},
        }
    )
    assert m.nav2_goal is not None
    assert m.nav2_goal["x"] == 1.0


def test_mission_plan_nav2_goal_invalid_becomes_none():
    m = MissionPlanV1.model_validate({"nav2_goal": "not-a-dict"})
    assert m.nav2_goal is None


def test_extract_invalid():
    with pytest.raises(ValueError):
        extract_json_object("no json here")
