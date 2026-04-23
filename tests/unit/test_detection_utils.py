"""Unit tests for boomy_mission_executor.detection_utils (path shim for CI without full ROS)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_PKG = _ROOT / "ros2" / "boomy_mission_executor"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from boomy_mission_executor.detection_utils import (  # noqa: E402
    extract_detection_labels,
    labels_match_target,
    tokenize_target,
)


def test_tokenize_target():
    toks = tokenize_target("German Shepherd dog named Benny")
    assert "german" in toks
    assert "shepherd" in toks
    assert "benny" in toks


def test_extract_detections_list():
    labels = extract_detection_labels([{"label": "dog", "score": 0.9}, {"class_name": "person"}])
    assert "dog" in labels
    assert "person" in labels


def test_extract_nested_keys():
    obj = {
        "detections": [
            {"label": "german_shepherd", "score": 0.8},
        ]
    }
    assert "german_shepherd" in extract_detection_labels(obj)


def test_labels_match_target():
    target = tokenize_target("find Benny")
    assert labels_match_target(["benny_the_dog"], target)
    assert not labels_match_target(["cat"], target)


def test_extract_invalid_string_returns_empty():
    assert extract_detection_labels("not json {") == []
