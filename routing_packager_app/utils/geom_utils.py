from typing import List, Tuple

from shapely.geometry import box, Polygon
from geoalchemy2.shape import to_shape, WKBElement


def bbox_to_wkt(bbox: List[float]) -> str:
    """
    Convert a bbox to WKT.

    :param bbox: the bbox as a list of floats in [minx, miny, maxx, maxy].

    :returns: WKT representation
    """
    return box(*bbox).wkt


def bbox_to_geom(bbox: List[float]) -> Polygon:
    """
    Convert a bbox to a shapely geometry.

    :param bbox: the bbox as a list of floats in [minx, miny, maxx, maxy].

    :returns: shapely Polygon
    """
    return box(*bbox)


def wkbe_to_geom(wkbe: WKBElement) -> Polygon:
    """
    Converts a geoalchemy2 :class:`WKBElement` to a shapely geometry.

    :param wkbe: The record.

    :returns: The shapely polygon
    """
    return to_shape(wkbe)


def wkbe_to_bbox(wkbe: WKBElement) -> Tuple[float]:
    """
    Converts a geoalchemy2 :class:`WKBElement` to a list of bbox coordinates.

    :param wkbe: The record.

    :returns: The bbox coordinates in [minx, miny, maxx, maxy].
    """
    return to_shape(wkbe).bounds


def wkbe_to_str(wkbe: WKBElement) -> str:
    """
    Converts a geoalchemy2 :class:`WKBElement` to a bbox string.

    :param wkbe: The record.

    :returns: The bbox string in [minx, miny, maxx, maxy] format.
    """
    return ",".join([str(f) for f in to_shape(wkbe).bounds])
