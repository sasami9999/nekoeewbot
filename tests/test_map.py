import logging

import map as map_module


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
