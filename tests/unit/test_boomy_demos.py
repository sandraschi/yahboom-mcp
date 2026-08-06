"""Boomy floor-draw and talkbot demo tests."""

from __future__ import annotations

import asyncio

import pytest

from yahboom_mcp.demo.draw_executor import get_draw_executor
from yahboom_mcp.demo.draw_patterns import list_patterns, pattern_layers
from yahboom_mcp.demo.talkbot import _extract_name, get_talkbot_demo
from yahboom_mcp.operations import demo_showcase


def test_list_patterns():
    out = list_patterns()
    assert out["success"] is True
    ids = {p["id"] for p in out["patterns"]}
    assert "smiley" in ids
    assert "boomy_b" in ids


def test_smiley_has_two_layers():
    layers = pattern_layers("smiley", speed=0.06)
    assert len(layers) == 2
    assert sum(len(layer["segments"]) for layer in layers) > 5


def test_extract_name():
    assert _extract_name("My name is Sandra") == "Sandra"
    assert _extract_name("I'm Alex") == "Alex"


@pytest.mark.mock
@pytest.mark.asyncio
async def test_demo_describe():
    out = await demo_showcase.execute("describe")
    assert out["success"] is True
    assert "draw" in out["demos"]
    assert "talkbot" in out["demos"]


@pytest.mark.mock
@pytest.mark.asyncio
async def test_draw_run_completes(mock_bridge, mock_ssh, monkeypatch):
    monkeypatch.setenv("YAHBOOM_DEMO_FAST", "1")
    ex = get_draw_executor()
    ex.status = "idle"
    ex._task = None
    out = await demo_showcase.execute("draw", pattern="boomy_b", skip_color_swap_pause=True)
    assert out["success"] is True
    assert ex._task is not None
    await asyncio.wait_for(ex._task, timeout=15.0)
    st = ex.get_status()
    assert st["status"] == "completed"


@pytest.mark.mock
@pytest.mark.asyncio
async def test_talkbot_scripted(mock_bridge, mock_ssh, monkeypatch):
    monkeypatch.setenv("YAHBOOM_DEMO_FAST", "1")
    tb = get_talkbot_demo()
    tb.status = "idle"
    tb._task = None
    out = await demo_showcase.execute(
        "talkbot",
        max_turns=2,
        use_speech_mcp=False,
        approach=False,
        scripted_user_lines=["My name is Guest", "Draw a picture"],
    )
    assert out["success"] is True
    await asyncio.wait_for(tb._task, timeout=20.0)
    st = tb.get_status()
    assert st["status"] == "completed"
    assert st["transcript"]
    assert any(t["role"] == "boomy" and "Boomy" in t["text"] for t in st["transcript"])
