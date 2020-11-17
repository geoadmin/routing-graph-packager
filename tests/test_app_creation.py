import pytest
from docker.errors import NullResource
import os

from routing_packager_app import CONF_MAPPER, create_app


def test_create_app():
    create_app('testing')


@pytest.mark.parametrize('flask_config_name', ['production', 'development', 'testing'])
def test_create_app_passing_flask_config_name(monkeypatch, flask_config_name):
    if flask_config_name != 'testing':
        from config import ProdConfig, DevConfig
        new_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        for c in (ProdConfig, DevConfig):
            monkeypatch.setattr(c, 'DATA_DIR', new_data_dir)
            monkeypatch.setattr(c, 'ENABLED_PROVIDERS', ["osm", "tomtom", "here"])
    create_app(config_string=flask_config_name)


def test_create_app_empty_config(monkeypatch):
    """Remove FLASK_CONFIG=testing"""
    if os.getenv('FLASK_CONFIG'):
        monkeypatch.delenv('FLASK_CONFIG')

    with pytest.raises(KeyError):
        create_app(config_string=None)


def test_create_app_with_broken_import_config(monkeypatch):
    CONF_MAPPER['broken-import-config'] = 'broken-import-config'
    if os.getenv('FLASK_CONFIG'):
        monkeypatch.delenv('FLASK_CONFIG')
    with pytest.raises(ImportError):
        create_app('broken-import-config')
    del CONF_MAPPER['broken-import-config']


def test_false_docker_image(monkeypatch):
    from config import TestingConfig
    monkeypatch.setattr(TestingConfig, 'ENABLED_ROUTERS', ['valhalla', 'graphhopper'])
    monkeypatch.setattr(TestingConfig, 'GRAPHHOPPER_IMAGE', '')
    with pytest.raises(NullResource):
        create_app('testing')
