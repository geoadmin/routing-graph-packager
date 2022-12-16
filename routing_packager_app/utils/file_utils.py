import os
import tarfile
import zipfile
from pathlib import Path
from typing import List


def make_directories(data_dir: str, temp_dir: str, routers: List[str]):
    """
    Creates the directories needed for the app to function properly.

    :param data_dir: the DATA_DIR env var
    :param temp_dir: the TEMP_DIR env var
    :param routers: the DATA_DIR env var
    """
    data_dir = data_dir
    for router in routers:
        os.makedirs(os.path.join(data_dir, router), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, router), exist_ok=True)


def make_package_path(base_dir: Path, name: str, router: str, provider: str, extension: str) -> Path:
    """
    Returns the file name from DATA_DIR, router, provider and dataset name.

    :param base_dir: The DATA_DIR env variable
    :param name: The dataset name, e.g. moldavia
    :param router: The router name, e.g. valhalla
    :param provider: The provider's name, e.g. osm
    :param extension: The package's compression, e.g. tar.gz

    :returns: The full path to the data package
    """
    file_name = "_".join([router, provider, name])

    # also create a folder with the same name
    out_dir = base_dir.joinpath(router, file_name)
    out_dir.mkdir(parents=True)

    return out_dir.joinpath(file_name + f".{extension}").resolve()


def make_tarfile(out_fp: str, source_dir: str):
    """
    Adds *source_dir* to a gzipped Tar file called *out_fp*.

    :param out_fp: full path to the resulting Tar file.
    :param source_dir: full path the directory which needs zipping.
    """
    with tarfile.open(out_fp, "w") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


# https://gist.github.com/felixSchl/d38b455df8bf83a78d3d
def make_zipfile(out_fp: str, source_dir: str):
    """
    Adds *source_dir* to a Zip file called *out_fp*.

    :param out_fp: full path to the resulting Zip file.
    :param source_dir: full path of the directory which needs zipping.
    """
    archive = zipfile.ZipFile(out_fp, "w", zipfile.ZIP_DEFLATED)
    if os.path.isdir(source_dir):
        _zippy(source_dir, source_dir, archive)
    else:
        _, name = os.path.split(source_dir)
        archive.write(source_dir, name)
    archive.close()


def _zippy(base_path, path, archive):
    paths = os.listdir(path)
    for p in paths:
        p = os.path.join(path, p)
        if os.path.isdir(p):
            _zippy(base_path, p, archive)
        else:
            archive.write(p, os.path.relpath(p, base_path))
