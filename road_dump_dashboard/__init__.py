# ---/ MXPACK-PART
from pathlib import Path

from .__mxp_version import get_version

__version__ = get_version(root=Path(__file__).parent.parent)
del get_version
# ---\ MXPACK-PART

# For now, put global env configuration here
import os

env_mxp_project_layout = os.getenv("MXP_PROJECT_LAYOUT", "version/mxp-recipe/project_layout.yml")
