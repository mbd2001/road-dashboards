from datetime import datetime

from dash import Input, Output, State, callback, dcc, html
from dash.dependencies import ALL

from road_dashboards.workflows_dashboard.core_settings.constants import (
    ComponentIds,
    WorkflowFields,
)
from road_dashboards.workflows_dashboard.database.workflow_manager import WorkflowsDBManager

db_manager = WorkflowsDBManager()


@callback(
    [
        Output(ComponentIds.ADDITIONAL_COLUMNS_CONTAINER, "style"),
        Output(ComponentIds.EXPORT_COLUMNS_SELECTOR, "options"),
    ],
    Input(ComponentIds.EXPORT_WORKFLOW_SELECTOR, "value"),
)
def update_columns_selector(selected_workflows):
    """Update the visibility and options of the columns selector."""
    if not selected_workflows or len(selected_workflows) != 1:
        return {"display": "none"}, []

    current_workflow = selected_workflows[0]
    current_workflow_columns = db_manager.get_workflow_columns(current_workflow)
    if len(current_workflow_columns) == 0:
        return {"display": "none"}, []

    # Get cloud columns if exist
    workflow_specific_columns = {WorkflowFields.exit_code, WorkflowFields.job_id, WorkflowFields.jira_key}
    additional_cols = [col for col in workflow_specific_columns if col in current_workflow_columns]
    column_options = [{"label": col, "value": col} for col in additional_cols]

    return {"display": "block"}, column_options


@callback(
    [
        Output(ComponentIds.EXPORT_COLUMN_VALUES_CONTAINER, "children"),
        Output(ComponentIds.EXPORT_STATUS_SELECTOR, "options"),
    ],
    [
        Input(ComponentIds.EXPORT_WORKFLOW_SELECTOR, "value"),
        Input(ComponentIds.EXPORT_COLUMNS_SELECTOR, "value"),
        Input(ComponentIds.BRAIN_SELECTOR, "value"),
        Input(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        Input(ComponentIds.DATE_RANGE_PICKER, "end_date"),
        Input(ComponentIds.EXPORT_STATUS_SELECTOR, "value"),
        Input({"type": "column-values", "column": ALL}, "value"),
    ],
    State({"type": "column-values", "column": ALL}, "id"),
)
def update_column_values_selectors(
    selected_workflows,
    selected_columns,
    brain_types,
    start_date,
    end_date,
    selected_statuses,
    column_values,
    column_ids,
):
    """Create value selectors for each selected column."""
    if not selected_workflows or len(selected_workflows) != 1:
        return [], []

    workflow = selected_workflows[0]

    # Build column filters from current selections
    column_filters = {}
    if column_ids and column_values:
        for col_id, values in zip(column_ids, column_values):
            if values:  # Only add filters that have selected values
                column_filters[col_id["column"]] = values

    # Get unique statuses with current filters
    unique_statuses = db_manager.get_unique_column_values(
        workflow, WorkflowFields.status, brain_types, start_date, end_date, None, column_filters
    )
    status_options = [{"label": status, "value": status} for status in unique_statuses]

    if not selected_columns:
        return [], status_options

    value_selectors = []

    for col in selected_columns:
        # Don't include the current column in filters when getting its options
        current_filters = {k: v for k, v in column_filters.items() if k != col}
        if selected_statuses:
            current_filters[WorkflowFields.status] = selected_statuses

        unique_values = db_manager.get_unique_column_values(
            workflow, col, brain_types, start_date, end_date, selected_statuses, current_filters
        )
        if unique_values:
            value_selector = html.Div(
                [
                    html.Label(f"Filter values for {col}", className="mb-2"),
                    dcc.Dropdown(
                        id={"type": "column-values", "column": col},
                        options=[{"label": val, "value": val} for val in unique_values],
                        value=column_filters.get(col),  # Preserve current selection if any
                        multi=True,
                        placeholder=f"Select values for {col}",
                        className="mb-3",
                    ),
                ],
                style={"position": "relative"},
            )
            value_selectors.append(value_selector)

    if value_selectors:  # Only add container styling if there are selectors
        return html.Div(
            value_selectors,
            style={
                "maxHeight": "300px",
                "overflowY": "auto",
                "padding": "10px",
                "border": "1px solid #dee2e6",
                "borderRadius": "4px",
                "backgroundColor": "#f8f9fa",
            },
        ), status_options
    return value_selectors, status_options


def _build_column_filters(selected_columns: list[str], column_values: list, column_ids: list) -> dict:
    """Build column filters dictionary from selected values.

    Args:
        selected_columns: List of selected column names
        column_values: List of selected values for each column
        column_ids: List of column IDs containing column names

    Returns:
        Dictionary mapping column names to their selected filter values
    """
    if not (selected_columns and column_values and column_ids):
        return {}

    column_filters = {}
    for values, col_id in zip(column_values, column_ids):
        if values:  # Only add filters for columns where values are selected
            column_filters[col_id["column"]] = values

    return column_filters


def _generate_export_filename(workflow_names: list[str]) -> str:
    """Generate a filename for the exported data.

    Args:
        workflow_names: List of workflow names to include in filename

    Returns:
        Generated filename with current date
    """
    current_date = datetime.now().strftime("%d-%m-%Y")
    return f"{'_'.join(workflow_names)}_data_{current_date}.csv"


@callback(
    Output(ComponentIds.DOWNLOAD_DATAFRAME, "data"),
    Input(ComponentIds.EXPORT_BUTTON, "n_clicks"),
    [
        State(ComponentIds.BRAIN_SELECTOR, "value"),
        State(ComponentIds.DATE_RANGE_PICKER, "start_date"),
        State(ComponentIds.DATE_RANGE_PICKER, "end_date"),
        State(ComponentIds.EXPORT_WORKFLOW_SELECTOR, "value"),
        State(ComponentIds.EXPORT_STATUS_SELECTOR, "value"),
        State(ComponentIds.EXPORT_COLUMNS_SELECTOR, "value"),
        State({"type": "column-values", "column": ALL}, "value"),
        State({"type": "column-values", "column": ALL}, "id"),
    ],
    prevent_initial_call=True,
)
def export_data(
    n_clicks,
    brain_types,
    start_date,
    end_date,
    selected_workflows,
    selected_statuses,
    selected_columns,
    column_values,
    column_ids,
):
    """Export data based on selected filters and columns."""
    if not n_clicks or not selected_workflows:
        return None

    # Only apply status and column filters for single workflow
    statuses = selected_statuses if len(selected_workflows) == 1 else None
    column_filters = (
        _build_column_filters(selected_columns, column_values, column_ids) if len(selected_workflows) == 1 else None
    )

    df = db_manager.get_workflow_export_data(
        selected_workflows, brain_types, start_date, end_date, statuses, column_filters
    )

    if df.empty:
        return None

    filename = _generate_export_filename(selected_workflows)
    return dcc.send_data_frame(df.to_csv, filename, index=False)
