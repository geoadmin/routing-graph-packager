import pytest

from app.core.geometries import geom_conversions


def test_bbox_to_geojson():
    bbox = [1.0, 2.0, 3.0, 4.0]

    gj = geom_conversions.bbox_to_geojson(bbox)

    print(gj)
    assert len(gj['coordinates'][0]) == 5


def test_bbox_to_geojson_error():
    bbox = [1, 2, 3]

    with pytest.raises(TypeError):
        geom_conversions.bbox_to_geojson(bbox)


def test_bbox_to_wkt():
    bbox = [1.0, 2.0, 3.0, 4.0]

    wkt = geom_conversions.bbox_to_wkt(bbox)

    assert wkt == 'POLYGON ((3 2, 3 4, 1 4, 1 2, 3 2))'


def test_bbox_to_wkt_error():
    bbox = [1, 2, 3]

    with pytest.raises(TypeError):
        geom_conversions.bbox_to_wkt(bbox)
