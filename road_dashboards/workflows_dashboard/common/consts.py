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


class ComponentIds:
    WORKFLOW_DATA_STORE = "workflow-data-store"
    STATUS_PIE_CHART = "status-pie-chart"
    ERROR_PIE_CHART = "error-pie-chart"
    WEEKLY_SUCCESS_RATE_CHART = "weekly-success-rate-chart"
    WORKFLOW_SUCCESS_COUNT_CHART = "workflow-success-count-chart"
    DATE_RANGE_PICKER = "date-range-picker"
    BRAIN_SELECTOR = "brain-selector"
    WORKFLOW_SELECTOR = "workflow-selector"
    STATUS_SELECTOR = "status-selector"
    LOADING_OVERLAY = "loading-overlay"
    MAIN_CONTENT = "main-content"
    REFRESH_DB_BUTTON = "refresh-db-button"


VALUE_SELECTOR_STYLE = {
    "maxHeight": "300px",
    "overflowY": "auto",
    "padding": "10px",
    "border": "1px solid #dee2e6",
    "borderRadius": "4px",
    "backgroundColor": "#f8f9fa",
}
