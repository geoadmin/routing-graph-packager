import pytest
from shapely.geometry import Polygon

from .utils import make_pbfs
from routing_packager_app.osmium import get_pbfs_by_area


def test_pbfs_by_area(tmpdir):
    # This will produce PBFs with bboxes in WGS84 degrees matching its features
    feats = {
        1: [[0, 0], [10, 10]],
        2: [[0, 0], [20, 20]],
        3: [[0, 0], [30, 30]],
    }

    paths = make_pbfs(tmpdir, feats)

    # A small polygon should return the smallest PBF
    paths_result = get_pbfs_by_area(tmpdir, Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]))
    assert len(paths_result) == 3
    assert paths_result[0][0] == paths[1]  # should be the pbf path with the smallest bbox from feats


def test_pbfs_by_area_missing_pbf(tmpdir):
    feats = {
        1: [[0, 0], [10, 10]],
    }

    make_pbfs(tmpdir, feats)

    with pytest.raises(FileNotFoundError) as e:
        get_pbfs_by_area(tmpdir, Polygon([(50, 50), (50, 100), (100, 100), (100, 50)]))
        assert "No PBF found for bbox" == str(e)
