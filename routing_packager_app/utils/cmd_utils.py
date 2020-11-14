import shlex
import subprocess

from shapely.geometry import Polygon


def osmium_extract_proc(bbox, in_pbf_path, out_pbf_path):
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

    return _exec_cmd(cmd)


def _exec_cmd(cmd):
    args = shlex.split(cmd)
    return subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
