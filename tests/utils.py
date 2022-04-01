import json
import os
from typing import List, Tuple  # noqa: F401

from flask import Response, current_app
from flask.testing import Client
from werkzeug.utils import cached_property
import osmium

from routing_packager_app.utils.cmd_utils import exec_cmd
from routing_packager_app.utils.file_utils import make_package_path

DEFAULT_ARGS_POST = {
    "name": "test",
    "description": "test description",
    "bbox": "0,0,1,1",
    "router": "valhalla",
    "provider": "osm",
    "interval": "once",
    "compression": "zip",
}


class JSONResponse(Response):
    # pylint: disable=too-many-ancestors
    """
    A Response class with extra useful helpers, i.e. ``.json`` property.
    """

    @cached_property
    def json(self):
        return json.loads(self.get_data(as_text=True))


def create_new_user(flask_app_client, data, auth_header, must_succeed=True):
    """
    Helper function for valid new user creation.
    """
    response = flask_app_client.post("/api/v1/users", headers=auth_header, data=data)

    if must_succeed:
        assert (
            response.status_code == 200
        ), f"status code was {response.status_code} with {response.data}"
        assert response.content_type == "application/json"
        assert set(response.json.keys()) >= {"id", "email"}
        return response.json["id"]
    return response


def create_new_job(client: Client, data, auth_header, must_succeed=True):
    """
    Helper function for valid new job creation.
    """
    response = client.post("/api/v1/jobs", headers=auth_header, data=data)

    if must_succeed:
        assert (
            response.status_code == 200
        ), f"status code was {response.status_code} with {response.data}"
        assert response.content_type == "application/json"
        return response.json
    return response


def make_pbfs(dirname, feats):
    """
    Creates PBFs in the specified directory from a dict of {id: [[x1, y1],[x2, y2]]}.

    :param str dirname: The output directory path
    :param dict feats: The virtual OSM features' coordinates in a dictionary.
        The keys will be the same as in the output.

    :returns: The dictionary with same keys as the input and the resulting full PBF paths as values.
    :rtype: dict
    """

    pbf_paths = dict()

    extract_cmd = "osmium extract --bbox {bbox} -o {out_file} {in_file} --set-bounds"
    for i, e in feats.items():
        fn = f"{i}.pbf"
        fp = str(dirname / fn)
        writer = OSMWriter(fp)
        for idx, node in enumerate(e):
            writer.add_node(idx, node)
        writer.close()

        # when extracting it sets the bounds we need
        fn_e = f"new_{fn}"
        fp_e = str(dirname / fn_e)
        bbox_str = ",".join([str(x) for x in (*e[0], *e[1])])
        proc = exec_cmd(extract_cmd.format(bbox=bbox_str, out_file=fp_e, in_file=fp))
        proc.wait()
        os.remove(fp)

        pbf_paths[i] = fp_e

    return pbf_paths


class OSMWriter(osmium.SimpleHandler):
    """Osmium Handler to write features to OSM file."""

    OSM_BASIC = {"version": 1, "changeset": 1, "timestamp": "2019-08-21T17:40:04Z"}

    def __init__(self, out_path):
        """
        Writes nodes, ways (and relations) to a user defined OSM file.

        :param out_path: Full path for the output file. The file ending determines the file format, .xml/.pbf.
        :type out_path: str
        """
        super(OSMWriter, self).__init__()
        self.writer = osmium.SimpleWriter(str(out_path))

    def add_node(self, id, location):
        """
        Writes a node to the OSM file.

        :param int id: Optional ID to give to node. Important for junction nodes. Simple integer if not provided.
        :param List[float]|Tuple[float] location: X, Y tuple of node
        """
        node = osmium.osm.mutable.Node(location=location, id=id, **self.OSM_BASIC)

        self.writer.add_node(node)

    def add_way(self, id, node_ids, tags):
        """
        Writes a way to the OSM file.

        :param List[int]|Tuple[int] node_ids: List of ID of nodes in geographical order.
        :param dict tags: OSM tags to give to the way. Values have to be casted to string.
        """

        way = osmium.osm.mutable.Way(nodes=node_ids, tags=tags, id=id, **self.OSM_BASIC)
        self.writer.add_way(way)

    def add_relation(self, id, members, tags=None):
        """
        Writes a relation to the OSM file.

        :param List[Tuple[str, str, str]] members: list of members accepted by osmium.osm.mutable.Relation in the form:
            [(type, id, role), (type, id, role), ...]
        :param dict tags: OSM tags
        """

        relation = osmium.osm.mutable.Relation(members=members, tags=tags, id=id, **self.OSM_BASIC)
        self.writer.add_relation(relation)

    def close(self):
        self.writer.close()


def create_package_params(j):
    """
    Create the parameters for create_package task

    :param dict j: The job response in JSON

    :returns: Tuple with all parameters inside
    :rtype: tuple
    """
    data_dir = current_app.config["DATA_DIR"]

    result_path = make_package_path(data_dir, j["name"], j["router"], j["provider"], j["compression"])

    return (
        j["id"],
        j["name"],
        j["description"],
        j["router"],
        j["provider"],
        [float(x) for x in j["bbox"].split(",")],
        result_path,
        j["pbf_path"],
        j["compression"],
        current_app.config["ADMIN_EMAIL"],
    )
