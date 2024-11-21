from dataclasses import dataclass
from enum import Enum

WORKFLOWS = ["drone_view_workflow", "gtrm_workflow", "emdp_workflow"]
BRAIN_OPTIONS = ["8mp", "wono", "mono"]
DEFAULT_BRAIN = "8mp"


class ComponentIds:
    WORKFLOW_DATA_STORE = "workflow-data-store"
    STATUS_PIE_CHART = "status-pie-chart"
    ERROR_PIE_CHART = "error-pie-chart"
    WEEKLY_SUCCESS_RATE_CHART = "weekly-success-rate-chart"
    DATE_RANGE_PICKER = "date-range-picker"
    EXPORT_BUTTON = "export-button"
    EXPORT_ALL_DATA = "export-all-data"
    DOWNLOAD_DATAFRAME = "download-dataframe-csv"
    BRAIN_SELECTOR = "brain-selector"
    WORKFLOW_SELECTOR = "workflow-selector"
    EXPORT_WORKFLOW_SELECTOR = "export-workflow-selector"
    LOADING_OVERLAY = "loading-overlay"
    MAIN_CONTENT = "main-content"


@dataclass
class WorkflowFields:
    status: str = "status"
    message: str = "message"
    last_update: str = "last_update"
    brain_type: str = "brain_type"
    clip_name: str = "clip_name"
    exit_code: str = "exit_code"


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    UNPROCESSED = "UNPROCESSED"


class LoadingStyles:
    overlay: dict = {
        "position": "fixed",
        "width": "100%",
        "height": "100%",
        "top": 0,
        "left": 0,
        "backgroundColor": "rgba(255, 255, 255, 0.7)",
        "zIndex": 999,
    }

    spinner: dict = {
        "position": "fixed",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
        "zIndex": 1000,
    }

    hidden: dict = {"display": "none"}

    blurred_content: dict = {"filter": "blur(3px)"}

    normal_content: dict = {}
