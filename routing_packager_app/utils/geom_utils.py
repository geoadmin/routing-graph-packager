from typing import List

from shapely.geometry import box, mapping, Polygon
from geoalchemy2.shape import to_shape, WKBElement
from pyproj import Transformer, CRS

WGS_TO_MOLLWEIDE = Transformer.from_crs(
    CRS.from_authority('EPSG', 4326), CRS.from_authority('ESRI', 54009), always_xy=True
).transform


def bbox_to_wkt(bbox):
    """
    Convert a bbox to WKT.

    :param List[float] bbox: the bbox as a list of floats in [minx, miny, maxx, maxy].

    :returns: WKT representation
    :rtype: str
    """
    return box(*bbox).wkt


def bbox_to_geom(bbox):
    """
    Convert a bbox to a shapely geometry.

    :param List[float] bbox: the bbox as a list of floats in [minx, miny, maxx, maxy].

    :returns: shapely Polygon
    :rtype: Polygon
    """
    return box(*bbox)


def wkbe_to_geom(wkbe):
    """
    Converts a geoalchemy2 :class:`WKBElement` to a shapely geometry.

    :param WKBElement wkbe: The record.

    :returns: The shapely polygon
    :rtype: Polygon
    """
    return to_shape(wkbe)
