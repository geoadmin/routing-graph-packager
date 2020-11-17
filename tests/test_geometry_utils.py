import pytest

from routing_packager_app.utils import geom_utils


def test_bbox_to_wkt():
    bbox = [1.0, 2.0, 3.0, 4.0]

    wkt = geom_utils.bbox_to_wkt(bbox)

    assert wkt == 'POLYGON ((3 2, 3 4, 1 4, 1 2, 3 2))'


def test_bbox_to_wkt_error():
    bbox = [1, 2, 3]

    with pytest.raises(TypeError):
        geom_utils.bbox_to_wkt(bbox)
