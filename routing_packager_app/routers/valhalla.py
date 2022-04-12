import json
import os
from collections import defaultdict
from flask import current_app

from .router_base import RouterBase
from ..constants import Routers, Compressions
from ..utils.file_utils import make_tarfile, make_zipfile


class Valhalla(RouterBase):
    """Valhalla implementation"""

    def name(self):
        return Routers.VALHALLA.value

    def build_graph(self):
        # tile_dir is the only required config
        config = defaultdict(dict)
        config["mjolnir"]["tile_dir"] = os.path.join(self._docker_graph_dir, "valhalla_tiles")

        # Add optional things, don't test for now
        valhalla_host_dir = os.path.join(current_app.config["DATA_DIR"], "valhalla")

        admin_path = os.path.join(valhalla_host_dir, "admins.sqlite")  # pragma: no cover
        if os.path.exists(admin_path):
            config["mjolnir"]["admin"] = "/app/data/valhalla/admins.sqlite"
            config["mjolnir"]["data_processing"] = {"use_admin_db": True}

        timezone_path = os.path.join(valhalla_host_dir, "timezones.sqlite")  # pragma: no cover
        if os.path.exists(timezone_path):
            config["mjolnir"]["timezone"] = "/app/data/valhalla/timezones.sqlite"

        elevation_path = os.path.join(valhalla_host_dir, "elevation")  # pragma: no cover
        if os.path.exists(elevation_path):
            config["additional_data"]["elevation"] = "/app/data/valhalla/elevation"

        # Stitch command and add inline config
        cmd = (
            f"sudo valhalla_build_tiles --inline-config '{json.dumps(config)}'"
            f" {self._docker_pbf_path}"
        )

        return self._exec_docker(cmd)

    def make_package(self, out_path, compression):
        if compression == Compressions.ZIP.value:
            make_zipfile(out_path, self._graph_dir)
        elif compression == Compressions.TAR.value:
            in_path = os.path.join(self._graph_dir, "valhalla_tiles")
            make_tarfile(out_path, in_path)
