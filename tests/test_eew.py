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
    event_id=None,
):
    payload = {
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
    if event_id is not None:
        payload["id"] = event_id
    return payload


@pytest.fixture(autouse=True)
def reset_eew_runtime_state():
    eew._last_userquake_by_area.clear()
    eew._seen_event_ids.clear()
    yield
    eew._last_userquake_by_area.clear()
    eew._seen_event_ids.clear()


@pytest.fixture
def mock_create_map(monkeypatch):
    def fake_create_map(_logger, _lat, _lon):
        return types.SimpleNamespace(filename="map_test.png")

    monkeypatch.setattr(eew.eq_map, "createMap", fake_create_map)


def test_scale_to_string():
    assert eew.scaleToString(10) == "1"
    assert eew.scaleToString(45) == "5弱"
    assert eew.scaleToString(50) == "5強"
    assert eew.scaleToString(999) == "不明"


def test_effective_to_string():
    assert eew.effectiveToString("None") == "なし"
    assert eew.effectiveToString("Watch") == "津波注意報"
    assert eew.effectiveToString("UnKnown") == "不明"


def test_env_int_defaults_and_invalid(monkeypatch):
    monkeypatch.delenv("MIN_NOTIFY_SCALE", raising=False)
    monkeypatch.delenv("MIN_NORTIFY_SCALE", raising=False)
    monkeypatch.setenv("MIN_MENTION_SCALE", "not-a-number")
    assert eew.envInt("MIN_NOTIFY_SCALE", 30) == 30
    assert eew.envInt("MIN_MENTION_SCALE", 50) == 50


def test_notify_scale_prefers_corrected_env_name(monkeypatch):
    monkeypatch.setenv("MIN_NORTIFY_SCALE", "10")
    monkeypatch.setenv("MIN_NOTIFY_SCALE", "40")
    assert eew.envInt("MIN_NOTIFY_SCALE", eew.envInt("MIN_NORTIFY_SCALE", 30)) == 40


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


def test_format_data_554_detection_returns_none(mock_create_map):
    embed, map_file, mention = eew.formatData(
        logger, {"code": 554, "type": "Full"}
    )
    assert embed is None
    assert map_file is None
    assert mention is False


def test_format_data_sends_without_map_when_create_map_fails(monkeypatch):
    monkeypatch.setattr(eew.eq_map, "createMap", lambda *_args, **_kwargs: None)
    embed, map_file, mention = eew.formatData(logger, sample_quake(code=551, max_scale=40))
    assert embed is not None
    assert map_file is None
    assert mention is False
    assert embed.image is None or getattr(embed.image, "url", None) in (None, "")


def test_userquake_cooldown_applies_only_after_mark(mock_create_map):
    payload = {"code": 561, "area": 250, "time": "2023/04/01 12:00:00.123"}
    first, _, _ = eew.formatData(logger, payload)
    second_before_mark, _, _ = eew.formatData(logger, payload)
    assert first is not None
    assert second_before_mark is not None

    eew.markUserquakeNotified(250)
    third_after_mark, _, _ = eew.formatData(logger, payload)
    assert third_after_mark is None


def test_duplicate_event_id_is_detected():
    assert eew.isDuplicateEvent("abc") is False
    assert eew.isDuplicateEvent("abc") is True
    assert eew.isDuplicateEvent(None) is False
    assert eew.isDuplicateEvent("") is False


def test_parse_time_uses_jst():
    from datetime import timezone

    dt = eew.parseTime("2023/04/01 12:00:00")
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == 9 * 3600
    assert dt.hour == 12
    assert dt.astimezone(timezone.utc).hour == 3


def test_parse_time_with_milliseconds_uses_jst():
    dt = eew.parseTime("2023/04/01 12:00:00.123")
    assert dt.tzinfo is not None
    assert dt.utcoffset().total_seconds() == 9 * 3600
    assert dt.microsecond == 123000


def test_embed_timestamp_keeps_jst_instant(mock_create_map):
    embed, _, _ = eew.formatData(
        logger, sample_quake(code=551, max_scale=40, time_str="2023/04/01 12:00:00")
    )
    assert embed is not None
    assert embed.timestamp is not None
    assert embed.timestamp.utcoffset().total_seconds() == 9 * 3600
    assert embed.timestamp.hour == 12
