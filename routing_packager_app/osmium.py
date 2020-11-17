import os
from typing import List

import osmium
from shapely.geometry import box, Polygon
from shapely.ops import transform
from pyproj import Transformer, CRS

from .utils.cmd_utils import exec_cmd

TRANSFORMATION = Transformer.from_crs(
    CRS.from_authority('EPSG', 4326), CRS.from_authority('ESRI', 54009), always_xy=True
).transform


def get_pbfs_by_area(pbf_dir, job_bbox):
    """
    Returns a list of [pbf_path, pbf_area] sorted by area.

    `osmium extract` is an expensive computation, so we want to keep
    the file size low. Here we find the PBF file which has the lowest
    file size but still completely fits the bbox.

    :param str pbf_dir: Directory for this provider.ü
    :param Polygon job_bbox: The new package's bbox

    :raises: FileNotFoundError
    :raises: AttributeError

    :returns: The full path of the PBF file which fits the job's bbox and has the smallest area
    :rtype: List[List[str, int]]
    """
    job_bbox_proj = transform(TRANSFORMATION, job_bbox)
    pbf_bbox_areas = {}
    for fn in os.listdir(pbf_dir):
        if not fn.endswith('.pbf'):
            continue

        fp = os.path.join(pbf_dir, fn)
        pbf_bbox_osmium = osmium.io.Reader(fp).header().box()
        assert pbf_bbox_osmium.valid(), f"Bounding box of PBF file {fp} is not valid."

        pbf_bbox_geom: Polygon = box(
            pbf_bbox_osmium.bottom_left.lon,
            pbf_bbox_osmium.bottom_left.lat,
            pbf_bbox_osmium.top_right.lon,
            pbf_bbox_osmium.top_right.lat,
        )
        pbf_bbox_proj = transform(TRANSFORMATION, pbf_bbox_geom)
        # Only keep the PBF bboxes which contain the job's bbox
        if not pbf_bbox_proj.contains(job_bbox_proj):
            continue
        pbf_bbox_areas[fp] = pbf_bbox_proj.area

    if not pbf_bbox_areas:
        raise FileNotFoundError(f"No PBF found for bbox {job_bbox}.")

    # Return the filepath with the minimum area of the matching ones
    return sorted(pbf_bbox_areas.items(), key=lambda x: x[1])


def extract_proc(bbox, in_pbf_path, out_pbf_path):
    """
    Returns a :class:`subprocess.Popen` instance to use osmium to cut a PBF to a bbox.

    :param Polygon bbox: The bbox as a DB WKBElement.
    :param str out_pbf_path: The full path the cut PBF should be saved to.
    :param str in_pbf_path: The full path of the input PBF.

    :returns: The subprocess calling osmium.
    :rtype: subprocess.Popen
    """
    minx, miny, maxx, maxy = bbox.bounds

    cmd = f"osmium extract --set-bounds --strategy=complete_ways --bbox={minx},{miny},{maxx},{maxy} -o {out_pbf_path} -O {in_pbf_path}"

    return exec_cmd(cmd)
