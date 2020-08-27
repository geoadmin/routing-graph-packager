import os
import json
import logging

from flask import current_app
from werkzeug.exceptions import InternalServerError
import docker
from docker.errors import ImageNotFound

docker_clnt = docker.from_env()
log = logging.getLogger(__name__)


class Valhalla(object):

    NAME = 'valhalla'
    TMP_DIR = f'/tmp/{NAME}'

    def __init__(self, input_pbf_path):
        self._docker_pbf_path = os.path.join(self.temp_dir, os.path.basename(input_pbf_path))
        self._docker_tiles_dir = os.path.join(self.temp_dir, 'tiles')
        self._docker_graph_dir = os.path.join(self.temp_dir, 'graph')
        self._graph_dir = os.path.join(current_app.config['GRAPH_DIR'], self.name)
        self._container_id = None
        self._volumes = {
            input_pbf_path: {
                'bind': self._docker_pbf_path,
                'mode': 'ro'
            },
            self._graph_dir: {
                'bind': self._docker_graph_dir,
                'mode': 'rw'
            }
        }

    def build_graph(self):
        if os.path.exists(self._docker_graph_dir):
            os.remove(self._docker_graph_dir)
        config = {"mjolnir": {"tile_dir": self._docker_graph_dir}}

        cmd = f"valhalla_build_tiles --inline-config '{json.dumps(config)}' {self._docker_pbf_path}"
        return self._exec_docker(cmd, volumes=self._volumes)

    def _exec_docker(self, cmd, **kwargs):
        try:
            container = docker_clnt.containers.create(self.image, **kwargs)
            self._container_id = container.id
        except ImageNotFound:
            raise InternalServerError(f"Docker image {self.image} not found for '{self.name}'")

        container.start()
        exit_code, output = container.exec_run(cmd)
        container.stop()
        container.remove()

        return exit_code, output

    @property
    def name(self):
        return self.NAME

    @property
    def image(self):
        return current_app.config[f'{self.NAME.upper()}_IMAGE']

    @property
    def temp_dir(self):
        return self.TMP_DIR

    @property
    def container_id(self):
        return self._container_id
