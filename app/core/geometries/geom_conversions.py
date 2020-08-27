from typing import List

from shapely.geometry import box, mapping
from geoalchemy2.shape import to_shape, WKBElement


def wkbe_to_geojson(wkbe: WKBElement):
    geom = to_shape(wkbe)
    return mapping(geom)


def bbox_to_geojson(bbox):
    """
    Converts a list of (minx,miny,maxx,maxy) coordinates into a GeoJSON polygon.

    :param List[float] bbox: list in format minx,miny,maxx,maxy

    :returns: GeoJSON Polygon
    :rtype: dict
    """
    return mapping(box(*bbox))


def bbox_to_wkt(bbox):
    return box(*bbox).wkt
