import os
from math import floor
from pathlib import Path

from routing_packager_app.api_v1.dependencies import split_bbox
from routing_packager_app.utils.valhalla_utils import TILE_SIZES, get_tiles_with_bbox

TAR_PATH_LENGTHS = [6, 6, 9]  # how many leading 0's do we need as tar file name?


def tile_base_to_path(base_x: int, base_y: int, level: int, fake_dir: Path) -> Path:
    """Convert a tile's base lat/lon to a relative tile path."""
    tile_size = TILE_SIZES[level]

    # assert we got no bogus tile base..
    assert (base_x + 180) % tile_size == 0 and (
        base_y + 90
    ) % tile_size == 0, f"{base_x}, {base_y} on level {level} failed"

    row = floor((base_y + 90) / tile_size)
    col = floor((base_x + 180) / tile_size)

    tile_id = int((row * 360 / tile_size) + col)

    path = (
        str(level)
        + "{:,}".format(int(pow(10, TAR_PATH_LENGTHS[level])) + tile_id).replace(",", os.sep)[1:]
    )

    return fake_dir.joinpath(path + ".gph")


def test_tile_intersects_bbox():
    # bogus tile dir
    tile_dir = Path("/home/")

    # bbox with which to filter the tile paths
    bbox = "10.2,53.9,20,59.2"
    input_paths = [
        tile_base_to_path(*input_tuple, tile_dir)
        for input_tuple in (
            (8, 50, 0),  # barely intersecting in the lower left
            (12, 54, 1),  # contained in bbox
            (20, 59, 2),  # barely intersecting in the upper right
        )
    ]
    out_paths = get_tiles_with_bbox(input_paths, split_bbox(bbox), tile_dir)
    assert sorted(input_paths) == sorted(out_paths)

    bbox = "-20,-59.2,-10.2,-53.9"
    input_paths = [
        tile_base_to_path(*input_tuple, tile_dir)
        for input_tuple in (
            (-20, -59, 2),  # barely intersecting in the lower left
            (-12, -54, 1),  # contained in bbox
            (-12, -62, 0),
        )
    ]
    out_paths = get_tiles_with_bbox(input_paths, split_bbox(bbox), tile_dir)
    assert sorted(input_paths) == sorted(out_paths)

    # don't find the ones not intersecting
    bbox = "0,10,4,14"
    input_paths = [
        tile_base_to_path(*input_tuple, tile_dir) for input_tuple in ((8, 14, 0), (-0.50, 9.75, 2))
    ]
    out_paths = get_tiles_with_bbox(input_paths, split_bbox(bbox), tile_dir)
    assert out_paths == set()
