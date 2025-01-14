from road_dashboards.workflows_dashboard.core_settings.constants import WorkflowFields


class ExportComponentsIds:
    EXPORT_BUTTON = "export-button"
    EXPORT_PREVIEW_BUTTON = "export-preview-button"
    EXPORT_PREVIEW_MODAL = "export-preview-modal"
    EXPORT_PREVIEW_TABLE = "export-preview-table"
    EXPORT_ALL_DATA = "export-all-data"
    EXPORT_WORKFLOW_SELECTOR = "export-workflow-selector"
    EXPORT_STATUS_SELECTOR = "export-status-selector"
    EXPORT_COLUMNS_SELECTOR = "export-columns-selector"
    EXPORT_COLUMN_VALUES_CONTAINER = "export-column-values-container"
    EXPORT_COLUMN_VALUES_SELECTOR = "export-column-values-selector"
    DOWNLOAD_DATAFRAME = "download-dataframe-csv"
    ADDITIONAL_COLUMNS_CONTAINER = "additional-columns-container"


WORKFLOW_SPECIFIC_COLUMNS = {WorkflowFields.exit_code, WorkflowFields.job_id, WorkflowFields.jira_key}
VALUE_SELECTOR_STYLE = {
    "maxHeight": "300px",
    "overflowY": "auto",
    "padding": "10px",
    "border": "1px solid #dee2e6",
    "borderRadius": "4px",
    "backgroundColor": "#f8f9fa",
}
