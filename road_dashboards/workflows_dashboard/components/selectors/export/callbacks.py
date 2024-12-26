from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from dash import Input, Output, State, callback, dcc, html
from dash.dependencies import ALL

from road_dashboards.workflows_dashboard.core_settings.constants import WorkflowFields,ComponentIds
from road_dashboards.workflows_dashboard.components.selectors.export.export_constants import ExportComponentsIds,WORKFLOW_SPECIFIC_COLUMNS,VALUE_SELECTOR_STYLE
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager

db_manager = WorkflowsDBManager()


@callback(
    [
        Output(ExportComponentsIds.ADDITIONAL_COLUMNS_CONTAINER, "style"),
        Output(ExportComponentsIds.EXPORT_COLUMNS_SELECTOR, "options"),
    ],
    Input(ExportComponentsIds.EXPORT_WORKFLOW_SELECTOR, "value"),
)
def update_columns_selector(selected_workflows: Optional[List[str]]) -> Tuple[Dict, List]:
    """Update column selector visibility and options based on selected workflow.
    
    Shows additional columns only when a single workflow is selected.
    """
    if not selected_workflows or len(selected_workflows) != 1:
        return {"display": "none"}, []

    workflow_columns = db_manager.get_workflow_columns(selected_workflows[0])
    if not workflow_columns:
        return {"display": "none"}, []

    additional_cols = [col for col in WORKFLOW_SPECIFIC_COLUMNS if col in workflow_columns]
    column_options = [{"label": col, "value": col} for col in additional_cols]

    return {"display": "block"}, column_options


def create_value_selector(col: str, unique_values: List, current_value: Optional[List] = None) -> html.Div:
    """Create a dropdown selector for filtering column values."""
    return html.Div(
        [
            html.Label(f"Filter values for {col}", className="mb-2"),
            dcc.Dropdown(
                id={"type": "column-values", "column": col},
                options=[{"label": val, "value": val} for val in unique_values],
                value=current_value,
                multi=True,
                placeholder=f"Select values for {col}",
                className="mb-3",
            ),
        ],
        style={"position": "relative"},
    )


@callback(
    [
        Output(ExportComponentsIds.EXPORT_COLUMN_VALUES_CONTAINER, "children"),
        Output(ExportComponentsIds.EXPORT_STATUS_SELECTOR, "options"),
    ],
    [
        Input(ExportComponentsIds.EXPORT_WORKFLOW_SELECTOR, "value"),
        Input(ExportComponentsIds.EXPORT_COLUMNS_SELECTOR, "value"),
        Input(ComponentIds.BRAIN_SELECTOR, "value"),
        Input(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        Input(ComponentIds.DATE_RANGE_PICKER, "end_date"),
        Input(ExportComponentsIds.EXPORT_STATUS_SELECTOR, "value"),
        Input({"type": "column-values", "column": ALL}, "value"),
    ],
    State({"type": "column-values", "column": ALL}, "id"),
)
def update_column_values_selectors(
    selected_workflows: Optional[List[str]],
    selected_columns: Optional[List[str]],
    brain_types: Optional[List[str]],
    start_date: Optional[str],
    end_date: Optional[str],
    selected_statuses: Optional[List[str]],
    column_values: List,
    column_ids: List[Dict],
) -> Tuple[Union[html.Div, List], List[Dict]]:
    """Update value selectors for columns and status options based on current selections."""
    if not selected_workflows or len(selected_workflows) != 1:
        return [], []

    workflow = selected_workflows[0]
    allowed_values = _build_allowed_values_per_column(selected_columns, column_values, column_ids)

    # Get status options
    unique_statuses = db_manager.get_unique_column_values(
        workflow, WorkflowFields.status, brain_types, start_date, end_date, None, allowed_values
    )
    status_options = [{"label": status, "value": status} for status in unique_statuses]

    if not selected_columns:
        return [], status_options

    # Create value selectors for each column
    value_selectors = []
    for col in selected_columns:
        current_filters = {
            **{k: v for k, v in allowed_values.items() if k != col},
            **({"status": selected_statuses} if selected_statuses else {}),
        }

        unique_values = db_manager.get_unique_column_values(
            workflow, col, brain_types, start_date, end_date, selected_statuses, current_filters
        )
        if unique_values:
            value_selectors.append(create_value_selector(col, unique_values, allowed_values.get(col)))

    if not value_selectors:
        return [], status_options

    return html.Div(value_selectors, style=VALUE_SELECTOR_STYLE), status_options


def _build_allowed_values_per_column(
    selected_columns: Optional[List[str]], column_values: List, column_ids: List[Dict]
) -> Dict[str, List]:
    """Build column filters dictionary from selected values."""
    if not (selected_columns and column_values and column_ids):
        return {}

    return {
        col_id["column"]: values
        for values, col_id in zip(column_values, column_ids)
        if values
    }


@callback(
    Output(ExportComponentsIds.DOWNLOAD_DATAFRAME, "data"),
    Input(ExportComponentsIds.EXPORT_BUTTON, "n_clicks"),
    [
        State(ComponentIds.BRAIN_SELECTOR, "value"),
        State(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        State(ComponentIds.DATE_RANGE_PICKER, "end_date"),
        State(ExportComponentsIds.EXPORT_WORKFLOW_SELECTOR, "value"),
        State(ExportComponentsIds.EXPORT_STATUS_SELECTOR, "value"),
        State(ExportComponentsIds.EXPORT_COLUMNS_SELECTOR, "value"),
        State({"type": "column-values", "column": ALL}, "value"),
        State({"type": "column-values", "column": ALL}, "id"),
    ],
    prevent_initial_call=True,
)
def export_data(
    n_clicks: int,
    brain_types: Optional[List[str]],
    start_date: Optional[str],
    end_date: Optional[str],
    selected_workflows: Optional[List[str]],
    selected_statuses: Optional[List[str]],
    selected_columns: Optional[List[str]],
    column_values: List,
    column_ids: List[Dict],
) -> Optional[Dict]:
    """Export filtered workflow data to CSV."""
    if not n_clicks or not selected_workflows:
        return None

    is_single_workflow = len(selected_workflows) == 1
    filters = {
        "statuses": selected_statuses if is_single_workflow else None,
        "allowed_values": _build_allowed_values_per_column(selected_columns, column_values, column_ids)
        if is_single_workflow else None
    }

    df = db_manager.get_workflow_export_data(
        selected_workflows, brain_types, start_date, end_date, 
        filters["statuses"], filters["allowed_values"]
    )

    if df.empty:
        return None

    filename = f"{'_'.join(selected_workflows)}_data_{datetime.now().strftime('%d-%m-%Y')}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)
