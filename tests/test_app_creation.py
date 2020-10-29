import pytest
from docker.errors import NullResource
import os

from kadas_routing_http import CONF_MAPPER, create_app


def test_create_app():
    create_app('testing')


@pytest.mark.parametrize('flask_config_name', ['production', 'development', 'testing'])
def test_create_app_passing_flask_config_name(monkeypatch, flask_config_name):
    if flask_config_name != 'testing':
        from config import ProdConfig, DevConfig
        for c in (ProdConfig, DevConfig):
            monkeypatch.setattr(c, 'PBF_PATH', os.path.join('tests', 'data', 'andorra-200827.osm.pbf'))
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
    with pytest.raises(NullResource):
        create_app('testing')


def test_false_pbf_path(monkeypatch):
    from config import TestingConfig
    monkeypatch.setattr(TestingConfig, 'PBF_PATH', '/some/path')
    with pytest.raises(FileNotFoundError):
        create_app('testing')
