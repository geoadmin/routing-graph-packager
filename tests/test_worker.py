import pytest
from starlette.exceptions import HTTPException

from routing_packager_app import SETTINGS
from routing_packager_app.worker import create_package

DEFAULT_ARGS = {
    "ctx": "",
    "job_id": 1,
    "job_name": "test",
    "description": "test desc",
    "bbox": "5.9559,45.818,10.4921,47.8084",
    "zip_path": str(SETTINGS.DATA_DIR.joinpath("test", "test.zip")),
    "user_id": 1,
}

# TODO:
#  - spin up a small http server here in a parameterized test with 8002/3
#  - alter the default bbox to only intersect one of the andorra level 2 tiles


async def test_fail_no_valhalla():
    with pytest.raises(HTTPException) as e:
        await create_package("", 0, "", "", "", "", 0)

    assert e.value.status_code == 500
    assert "No Valhalla service online" in e.value.detail


async def test_fail_no_tiles_in_dir():
    with pytest.raises(HTTPException) as e:
        await create_package(**DEFAULT_ARGS)

    assert e.value.status_code == 404
    assert "No Valhalla tiles in bbox" in e.value.detail


async def test_fail_no_tiles_in_bbox():
    with pytest.raises(HTTPException) as e:
        await create_package(**DEFAULT_ARGS)

    assert e.value.status_code == 404
    assert "No Valhalla tiles in bbox" in e.value.detail
