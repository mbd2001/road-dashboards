from dataclasses import dataclass
from enum import Enum
from typing import Dict

# Workflows
WORKFLOWS = ["drone_view_workflow", "gtrm_workflow", "emdp_workflow"]

# Component IDs
WORKFLOW_DATA_STORE = "workflow-data-store"
STATUS_PIE_CHART = "status-pie-chart"
ERROR_PIE_CHART = "error-pie-chart"
WEEKLY_SUCCESS_RATE_CHART = "weekly-success-rate-chart"
DATE_RANGE_PICKER = "date-range-picker"
EXPORT_BUTTON = "export-button"
DOWNLOAD_DATAFRAME = "download-dataframe-csv"

BRAIN_OPTIONS = ["8mp", "wono", "mono"]
DEFAULT_BRAIN = "8mp"
BRAIN_SELECTOR = "brain-selector"
WORKFLOW_SELECTOR = "workflow-selector"
MAX_ERROR_MESSAGE_LENGTH = 45


@dataclass
class WorkflowFields:
    status = "status"
    message = "message"
    last_update = "last_update"
    brain_type = "brain_type"
    clip_name = "clip_name"
    exit_code = "exit_code"


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    EMPTY = ""


class StatusColors:
    SUCCESS = "#28a745"
    FAILED = "#dc3545"
    IN_PROGRESS = "#007bff"


class ChartConfig:
    title_font_size: int = 16
    default_colors: Dict[str, str] = {
        Status.SUCCESS.value: StatusColors.SUCCESS,
        Status.FAILED.value: StatusColors.FAILED,
        Status.IN_PROGRESS.value: StatusColors.IN_PROGRESS,
    }


@dataclass
class DBConfig:
    table_name: str = "algoroad_workflows"
    primary_key: str = WorkflowFields.clip_name
