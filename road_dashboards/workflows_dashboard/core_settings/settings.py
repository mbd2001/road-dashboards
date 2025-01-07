from dataclasses import dataclass
from typing import Dict

from road_dashboards.workflows_dashboard.core_settings.constants import Status


class ChartSettings:
    title_font_size: int = 16
    max_error_message_length: int = 30
    default_colors: Dict[str, str] = {
        Status.SUCCESS.value: "#28a745",
        Status.FAILED.value: "#dc3545",
        Status.IN_PROGRESS.value: "#007bff",
        Status.UNPROCESSED.value: "#ffc107",
    }
    marker_symbols: list[str] = ["circle", "square", "diamond", "triangle-up", "star"]


@dataclass
class DatabaseSettings:
    table_name: str = "algoroad_workflows"
    primary_key: str = "clip_name"
