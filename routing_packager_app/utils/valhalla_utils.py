from collections import namedtuple
from pathlib import Path
from typing import List, Set

from math import floor

Bbox = namedtuple("Bbox", "min_x min_y max_x max_y")
TILE_SIZES = {0: 4, 1: 1, 2: 0.25}


def get_tile_bbox(tile_path: Path) -> Bbox:
    """Returns a tile's bounding box in minx,miny,maxx,maxy format"""
    level, tile_idx = [int(x.replace("/", "")) for x in get_tile_level_id(str(tile_path))]

    tile_size = TILE_SIZES[level]
    row = floor(tile_idx / (360 / tile_size))
    col = tile_idx % (360 / tile_size)

    tile_base_y = (row * tile_size) - 90
    tile_base_x = (col * tile_size) - 180

    return Bbox(tile_base_x, tile_base_y, tile_base_x + tile_size, tile_base_y + tile_size)


def get_tiles_with_bbox(all_tile_paths: List[Path], bbox: List[float]) -> Set[Path]:
    tile_paths = set()
    bbox = Bbox(*bbox)
    for tile_path in all_tile_paths:
        tile_bbox: Bbox = get_tile_bbox(tile_path)
        # check if tile_bbox is outside bbox
        if not any(
            [
                tile_bbox.min_x < bbox.min_x and tile_bbox.max_x < bbox.min_x,  # left of bbox
                tile_bbox.min_y < bbox.min_y and tile_bbox.max_y < bbox.min_y,  # below bbox
                tile_bbox.min_x > bbox.max_x and tile_bbox.max_x > bbox.max_x,  # right of bbox
                tile_bbox.min_y > bbox.max_y and tile_bbox.max_y > bbox.max_y,  # above bbox
            ]
        ):
            tile_paths.add(tile_path)

    return tile_paths


def get_tile_level_id(path: str) -> List[str]:
    """Returns both level and tile ID"""
    return path[:-4].split("/", 1)
