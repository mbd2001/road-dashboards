# pylint: disable=missing-module-docstring
from setuptools import setup, find_namespace_packages


class SetupPyInfo:
    """Keeps info from meta yaml and version for setup py"""

    def __init__(self, meta_yaml, version):
        """creates SetupPyInfo instance

        Args:
            meta_yaml (dict): python dict-like-struct meta_yaml representation
            version (str): version for pypy package
        """
        self.meta_yaml = meta_yaml
        self.version = version

    @classmethod
    def from_mxpack(cls):
        """Creates SetupPyInfo instance

        Returns:
            [type]: [description]
        """
        # pylint: disable=import-outside-toplevel
        import json
        import subprocess

        # pylint: disable=fixme
        # TODO: Read from setup-py-settings.json
        out = subprocess.check_output("mxp_cli setup-py-info info-infer json", shell=True)
        setup_info_d = json.loads(out.strip())
        setup_info_m = cls(meta_yaml=setup_info_d["meta_yaml"], version=setup_info_d["version"])
        return setup_info_m


setup_info = SetupPyInfo.from_mxpack()

install_requires = ["pydantic", "fire", "pyyaml", "loguru", "orjson", "typing_extensions>=3.7.4"]

cfg = dict(
    name=setup_info.meta_yaml["package"]["name"],
    version=setup_info.version,
    packages=find_namespace_packages(exclude=["*__tests.py", "*__test.py", "test*"]),
    description=setup_info.meta_yaml["about"]["summary"],
    license=setup_info.meta_yaml["about"]["license"],
    author=setup_info.meta_yaml["about"]["author"],
    author_email=setup_info.meta_yaml["about"]["author_email"],
    url=setup_info.meta_yaml["about"]["home"],
    install_requires=install_requires,
    entry_points={"console_scripts": setup_info.meta_yaml["build"]["entry_points"]},
    include_package_data=True,
    # exclude non-py files here
    exclude_package_data={
        # placeholder
    },
)

setup(**cfg)
