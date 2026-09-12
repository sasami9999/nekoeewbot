import logging
import types

import pytest

import eew


logger = logging.getLogger("test")


def sample_quake(
    *,
    code=551,
    max_scale=40,
    latitude=35.0,
    longitude=139.0,
    magnitude=5.0,
    hypo_name="東京湾",
    time_str="2023/04/01 12:00:00",
    tsunami="None",
):
    return {
        "code": code,
        "earthquake": {
            "time": time_str,
            "maxScale": max_scale,
            "domesticTsunami": tsunami,
            "hypocenter": {
                "name": hypo_name,
                "latitude": latitude,
                "longitude": longitude,
                "magnitude": magnitude,
            },
        },
    }


@pytest.fixture
def mock_create_map(monkeypatch):
    def fake_create_map(_logger, _lat, _lon):
        return types.SimpleNamespace(filename="map_test.png")

    monkeypatch.setattr(eew.map, "createMap", fake_create_map)


def test_scale_to_string():
    assert eew.scaleToString(10) == "1"
    assert eew.scaleToString(45) == "5弱"
    assert eew.scaleToString(50) == "5強"
    assert eew.scaleToString(999) == "不明"


def test_effective_to_string():
    assert eew.effectiveToString("None") == "なし"
    assert eew.effectiveToString("Watch") == "津波注意報"
    assert eew.effectiveToString("UnKnown") == "不明"


def test_format_data_skips_below_notify_scale(mock_create_map):
    embed, map_file, mention = eew.formatData(logger, sample_quake(max_scale=20))
    assert embed is None
    assert map_file is None
    assert mention is False


def test_format_data_skips_invalid_coordinates(mock_create_map):
    embed, map_file, mention = eew.formatData(
        logger, sample_quake(max_scale=40, latitude=-200, longitude=-200)
    )
    assert embed is None
    assert map_file is None
    assert mention is False


def test_format_data_551_without_mention(mock_create_map):
    embed, map_file, mention = eew.formatData(logger, sample_quake(code=551, max_scale=40))
    assert embed is not None
    assert embed.title == "地震情報"
    assert "**最大震度: 4**" in embed.description
    assert map_file.filename == "map_test.png"
    assert mention is False


def test_format_data_551_with_mention(mock_create_map):
    embed, map_file, mention = eew.formatData(logger, sample_quake(code=551, max_scale=50))
    assert embed is not None
    assert embed.title == "地震情報"
    assert mention is True
    assert map_file is not None


def test_format_data_556_always_mentions(mock_create_map):
    embed, map_file, mention = eew.formatData(logger, sample_quake(code=556, max_scale=30))
    assert embed is not None
    assert embed.title == "緊急地震速報（警報）"
    assert mention is True
    assert map_file is not None


def test_format_data_unsupported_code(mock_create_map):
    embed, map_file, mention = eew.formatData(logger, {"code": 555})
    assert embed is None
    assert map_file is None
    assert mention is False


def test_format_data_554_warning_returns_none(mock_create_map):
    embed, map_file, mention = eew.formatData(
        logger, {"code": 554, "issue": {"type": "Warning"}}
    )
    assert embed is None
    assert map_file is None
    assert mention is False
