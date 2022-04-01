from routing_packager_app.constants import Routers
from .valhalla import Valhalla


def get_router(name, provider, cut_pbf_path):
    """
    Factory for router classes.

    :param str name: The router name, e.g. valhalla.
    :param str provider: The data provider, e.g. osm.
    :param str cut_pbf_path: The path to the input PBF.

    :returns: instantiated router object.
    :rtype: Valhalla
    """

    if name == Routers.VALHALLA.value:
        return Valhalla(provider, cut_pbf_path)
    else:
        return False
