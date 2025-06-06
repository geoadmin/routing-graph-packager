import pytest


# Only test for errors here, since successes are tested by the e2e tests
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from routing_packager_app.api_v1.dependencies import split_bbox, get_validated_name


@pytest.mark.parametrize("bbox", ("0;0;1;1", "0,2,3", "20,20,20,20", "20,30,40,30", "120,50,110,60"))
def test_split_bbox_fail(bbox):
    with pytest.raises((ValueError, HTTPException)):
        split_bbox(bbox)


@pytest.mark.parametrize("name", ("gut%", "/fal"))
def test_validate_names_fail(name):
    with pytest.raises(HTTPException) as e:
        get_validated_name(name)
    assert e.value.status_code == HTTP_400_BAD_REQUEST
