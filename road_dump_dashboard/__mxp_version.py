""" mxp projects version getter
this getter supports both py packages created with mxp
"""


def get_version(root=None):
    try:
        import importlib.resources as pkg_resources
        import json
        import zipfile
        from pathlib import Path

        def _read_version_from_build_info_zip(_build_info_zip_path):
            archive = zipfile.ZipFile(str(path_p), "r")
            with archive.open("__build_info/mxpack/conda_build__pre_build__info.json") as fp:
                version_info = json.load(fp)
                return version_info["package_version_name"]

        try:
            from . import _resources_

            with pkg_resources.path(_resources_, "__build_info.zip") as path_p:
                return _read_version_from_build_info_zip(path_p)
        except (FileNotFoundError, ImportError):
            root = root or Path(__file__).absolute()
            path_p = Path(root) / "_resources_" / "__build_info.zip"
            return _read_version_from_build_info_zip(path_p)
    except:
        # never raise exception in production
        return "no-version-found"
