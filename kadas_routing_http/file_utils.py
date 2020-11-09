import os
import tarfile
import zipfile


def make_tarfile(out_fp, source_dir):
    """
    Adds *source_dir* to a gzipped Tar file called *out_fp*.

    :param str out_fp: full path to the resulting Tar file.
    :param str source_dir: full path the directory which needs zipping.
    """
    with tarfile.open(out_fp + '.tar.gz', "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


# https://gist.github.com/felixSchl/d38b455df8bf83a78d3d
def make_zipfile(out_fp, source_dir):
    """
    Adds *source_dir* to a Zip file called *out_fp*.

    :param str out_fp: full path to the resulting Zip file.
    :param str source_dir: full path the directory which needs zipping.
    """
    archive = zipfile.ZipFile(out_fp + '.zip', "w", zipfile.ZIP_DEFLATED)
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
