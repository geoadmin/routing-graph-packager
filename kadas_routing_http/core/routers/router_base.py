import os
from abc import ABC, abstractmethod

from flask import current_app
from werkzeug.exceptions import InternalServerError
import docker
from docker.errors import ImageNotFound


class RouterBase(ABC):

    DOCKER_TMP = '/tmp'
    docker_clnt = docker.from_env()

    def __init__(self, input_pbf_path):
        self._input_pbf_path = input_pbf_path
        self._docker_pbf_path = os.path.join(self.DOCKER_TMP, os.path.basename(self._input_pbf_path))
        self._docker_tiles_dir = os.path.join(self.DOCKER_TMP, 'tiles')
        self._docker_graph_dir = os.path.join(self.DOCKER_TMP, 'graph')
        self._graph_dir = os.path.join(current_app.config['TEMP_DIR'], self.name(), 'graph')

        self._container = None
        self._volumes = {
            self._input_pbf_path: {
                'bind': self._docker_pbf_path,
                'mode': 'ro'
            },
            self._graph_dir: {
                'bind': self._docker_graph_dir,
                'mode': 'rw'
            }
        }

        # initialize the container to get the container ID
        self._init_docker(volumes=self._volumes)

    def _init_docker(self, **kwargs):
        """
        Initializes the Docker container on instance creation.

        :raises: InternalServerError
        """
        try:
            self._container = self.docker_clnt.containers.create(self.image, **kwargs)
        except ImageNotFound:
            raise InternalServerError(f"Docker image {self.image} not found for '{self.name}'")

    def _exec_docker(self, cmd):
        self._container.start()
        exit_code, output = self._container.exec_run(cmd)
        self._container.stop()
        # if os.getenv('FLASK_CONFIG') != 'development':
        #    self._container.remove()

        return exit_code, output

    def cleanup(self):
        self._container.remove()

    @property
    def image(self):
        return current_app.config[f'{self.name().upper()}_IMAGE']

    @property
    def container_id(self):
        return self._container.id

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def build_graph(self):
        pass
