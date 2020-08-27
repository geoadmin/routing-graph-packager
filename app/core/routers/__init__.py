from .valhalla import Valhalla
from typing import List


def get_router(name, cut_pbf_path):
    """
    Factory for router classes.

    :param str name: The router name, one of 'valhalla'.
    :param str cut_pbf_path:  The path to the input PBF.

    :returns: instantiated router object.
    :rtype: Valhalla
    """

    if name == 'valhalla':
        return Valhalla(cut_pbf_path)
    else:
        return False
