import pytest

from app import CONF_MAPPER, create_app


def test_create_app():
    create_app()


@pytest.mark.parametrize('flask_config_name', ['production', 'development', 'testing'])
def test_create_app_passing_flask_config_name(monkeypatch, flask_config_name):
    if flask_config_name != 'testing':
        from config import ProdConfig
        monkeypatch.setattr(ProdConfig, 'SQLALCHEMY_DATABASE_URI', 'sqlite://')
        monkeypatch.setattr(ProdConfig, 'SECRET_KEY', 'secret')
    create_app(config_string=flask_config_name)


def test_create_app_empty_config(monkeypatch):
    """Remove FLASK_CONFIG=testing"""
    monkeypatch.delenv('FLASK_CONFIG', raising=False)

    with pytest.raises(KeyError):
        create_app()


def test_create_app_with_broken_import_config():
    CONF_MAPPER['broken-import-config'] = 'broken-import-config'
    with pytest.raises(ImportError):
        create_app('broken-import-config')
    del CONF_MAPPER['broken-import-config']