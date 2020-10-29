from typing import List
import shlex
import subprocess


def osmium_extract_proc(bbox, in_pbf_path, out_pbf_path):
    """
    Returns a :class:`subprocess.Popen` instance to use osmium to cut a PBF to a bbox.

    :param List[float] bbox: The bbox as a list of floats in [minx, miny, maxx, maxy].
    :param str out_pbf_path: The full path the cut PBF should be saved to.
    :param str in_pbf_path: The full path of the input PBF.

    :returns: The subprocess calling osmium.
    :rtype: subprocess.Popen
    """
    minx, miny, maxx, maxy = bbox

    cmd = f"osmium extract --bbox={minx},{miny},{maxx},{maxy} -o {out_pbf_path} -O {in_pbf_path}"

    return _exec_cmd(cmd)


def _exec_cmd(cmd):
    args = shlex.split(cmd)
    return subprocess.Popen(args)
