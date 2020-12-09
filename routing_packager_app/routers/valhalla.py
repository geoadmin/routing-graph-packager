import json
import os
from collections import defaultdict

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
        config["mjolnir"]["tile_dir"] = os.path.join(self._docker_graph_dir, 'valhalla_tiles')

        # Add optional things, don't test for now
        valhalla_dir = os.path.join('/app', 'data', 'valhalla')

        admin_path = os.path.join(valhalla_dir, 'admins.sqlite')  # pragma: no cover
        if os.path.exists(admin_path):
            config['mjolnir']['admin'] = admin_path

        timezone_path = os.path.join(valhalla_dir, 'timezones.sqlite')  # pragma: no cover
        if os.path.exists(timezone_path):
            config['mjolnir']['timezone'] = timezone_path

        elevation_path = os.path.join(valhalla_dir, 'elevation')  # pragma: no cover
        if os.path.exists(timezone_path):
            config['additional_data']['elevation'] = elevation_path

        # Stitch command and add inline config
        cmd = f"valhalla_build_tiles --inline-config '{json.dumps(config)}'" \
              f" {self._docker_pbf_path}"
        return self._exec_docker(cmd)

    def make_package(self, out_path, compression):
        if compression == Compressions.ZIP.value:
            make_zipfile(out_path, self._graph_dir)
        elif compression == Compressions.TARGZ.value:
            in_path = os.path.join(self._graph_dir, 'valhalla_tiles')
            make_tarfile(out_path, in_path)
