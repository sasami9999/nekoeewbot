import logging
from unittest.mock import Mock

import map as map_module
import requests


logger = logging.getLogger("test")


def test_lat_lon_to_pixel_xy_returns_finite_values():
    x, y = map_module.latLonToPixelXY(35.681, 139.767, 9)
    assert x > 0
    assert y > 0
    assert x == x  # not NaN
    assert y == y


def test_create_red_cross_svg_contains_marker():
    global_pixel = map_module.latLonToPixelXY(35.681, 139.767, 9)
    # tile centers roughly matching createMap zoom/tile math is not required;
    # just verify SVG structure for a plausible center.
    svg = map_module.createRedCrossSVG(logger, 768, 450, 200, global_pixel)
    assert svg.startswith("<svg")
    assert 'stroke="red"' in svg
    assert "</svg>" in svg


def test_create_map_returns_none_when_tile_fetch_fails(monkeypatch):
    def fail_get(*_args, **_kwargs):
        raise requests.RequestException("tile unavailable")

    monkeypatch.setattr(map_module.requests, "get", fail_get)
    assert map_module.createMap(logger, 35.681, 139.767) is None


def test_create_map_returns_none_on_unexpected_error(monkeypatch):
    monkeypatch.setattr(
        map_module,
        "latLonToPixelXY",
        Mock(side_effect=RuntimeError("boom")),
    )
    assert map_module.createMap(logger, 35.681, 139.767) is None
