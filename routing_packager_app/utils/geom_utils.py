from typing import List

from shapely.geometry import box, mapping, Polygon
from geoalchemy2.shape import to_shape, WKBElement


def wkbe_to_geojson(wkbe):  # pragma: no cover
    """
    Converts a geoalchemy2 :class:`WKBElement` to a GeoJSON.

    :param WKBElement wkbe: The record.

    :returns: GeoJSON representation
    :rtype: dict
    """
    geom = to_shape(wkbe)
    return mapping(geom)


def bbox_to_geojson(bbox):
    """
    Converts a list of (minx,miny,maxx,maxy) coordinates into a GeoJSON polygon.

    :param List[float] bbox: the bbox as a list of floats in [minx, miny, maxx, maxy].

    :returns: GeoJSON Polygon
    :rtype: dict
    """
    return mapping(box(*bbox))


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


def wkbe_to_wkt(wkbe):
    """
    Converts a geoalchemy2 :class:`WKBElement` to a WKT.

    :param WKBElement wkbe: The record.

    :returns: WKT representation
    :rtype: str
    """
    return to_shape(wkbe).wkt
