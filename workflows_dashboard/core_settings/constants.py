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
    EMPTY = ""
