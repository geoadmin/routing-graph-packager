import os
from abc import ABC, abstractmethod

from flask import current_app
from werkzeug.exceptions import InternalServerError
import docker
from docker.errors import ImageNotFound

from ..constants import DOCKER_VOLUME

docker_clnt = docker.from_env()


class RouterBase(ABC):
    """
    Base class for all routers.

    Subclasses need to implement the abstract methods.
    """
    def __init__(self, provider, input_pbf_path):
        self._input_pbf_path = input_pbf_path
        self._graph_dir = os.path.join(current_app.config['TEMP_DIR'], self.name(), 'graph')
        self._container = None

        # It's important to maintain the same directory structure in docker, host etc
        self._docker_pbf_path = os.path.join(
            '/app', 'data', provider, os.path.basename(self._input_pbf_path)
        )
        self._docker_graph_dir = os.path.join('/app', 'data', 'temp', self.name(), 'graph')

        # if testing we need to reference the test data directory
        # else the previously created docker volume
        host_dir = docker_clnt.volumes.get(DOCKER_VOLUME
                                           ).name if not current_app.config['TESTING'] else os.path.join(
                                               current_app.root_path, '..', 'tests', 'data'
                                           )
        volumes = {host_dir: {'bind': '/app/data', 'mode': 'rw'}}
        try:
            self._container = docker_clnt.containers.create(self.image, volumes=volumes)
        except ImageNotFound:
            raise InternalServerError(f"Docker image {self.image} not found for '{self.name}'")

    def _exec_docker(self, cmd):
        """
        Executes the command sync in a docker container and stops it after.
        The container will be removed during cleanup.
        """
        self._container.start()
        exit_code, output = self._container.exec_run(cmd)

        return exit_code, output

    def cleanup(self):
        """Cleanup operations once the packaging was successful."""
        self._exec_docker(f"rm -r {self._docker_graph_dir}")
        self._container.stop()
        self._container.remove()

    @property
    def image(self):
        return current_app.config[f'{self.name().upper()}_IMAGE']

    @property
    def container_id(self):
        return self._container.id

    @property
    def graph_dir(self):
        return self._graph_dir

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def build_graph(self):
        pass
