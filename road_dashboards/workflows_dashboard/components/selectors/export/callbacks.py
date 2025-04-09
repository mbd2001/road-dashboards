from datetime import datetime

from dash import Input, Output, State, callback, callback_context, dcc, html
from dash.dependencies import ALL
from road_database_toolkit.databases.workflows.workflow_enums import WorkflowRunSpecificColumns, WorkflowType

from road_dashboards.workflows_dashboard.common.analytics import analytics_manager
from road_dashboards.workflows_dashboard.common.consts import VALUE_SELECTOR_STYLE, ComponentIds, ExportComponentsIds


@callback(
    [
        Output(ExportComponentsIds.ADDITIONAL_COLUMNS_CONTAINER, "hidden"),
        Output(ExportComponentsIds.EXPORT_COLUMNS_SELECTOR, "options"),
    ],
    Input(ExportComponentsIds.EXPORT_WORKFLOW_SELECTOR, "value"),
)
def update_columns_selector(selected_workflows: list[str] | None) -> tuple[bool, list[dict]]:
    """Update column selector visibility and options based on selected workflow.

    Shows additional columns only when a single workflow is selected.
    """
    if not selected_workflows or len(selected_workflows) != 1:
        return True, []
    workflow_enum = WorkflowType(selected_workflows[0])

    workflow_specific_columns = analytics_manager.get_specific_workflow_columns(workflow_enum)
    if not workflow_specific_columns:
        return True, []

    column_options = [{"label": col, "value": col} for col in workflow_specific_columns]

    return False, column_options


def create_value_selector(
    col: WorkflowRunSpecificColumns, unique_values: list[str], current_value: list[str] | None = None
) -> html.Div:
    """Create a larger dropdown selector for filtering column values."""
    return html.Div(
        [
            html.Label(f"Filter values for {col}", className="mb-4 text-lg font-medium"),
            dcc.Dropdown(
                id={"type": "column-values", "column": col},
                options=[{"label": val, "value": val} for val in unique_values],
                value=current_value,
                multi=True,
                placeholder=f"Select values for {col}",
                className="mb-8",
            ),
        ],
        style={
            "marginBottom": "10rem",
        },
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
def update_workflow_specific_column_values_selectors(
    selected_workflows: list[str] | None,
    selected_columns: list[str] | None,
    brain_types: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    selected_statuses: list[str] | None,
    column_values: list[list[str] | None],
    column_ids: list[dict],
) -> tuple[html.Div | list[dict], list[dict]]:
    """Update value selectors for columns and status options based on current selections."""
    if not selected_workflows or len(selected_workflows) != 1:
        return [], []

    workflow_enum = WorkflowType(selected_workflows[0])

    unique_statuses_enums = analytics_manager.get_unique_status_values(
        workflow_type=workflow_enum, brain_types=brain_types, start_date=start_date, end_date=end_date
    )
    status_options = [{"label": status.value, "value": status.value} for status in unique_statuses_enums]

    if not selected_columns:
        return [], status_options

    allowed_values = _build_allowed_values_per_column(selected_columns, column_values, column_ids)

    value_selectors = []
    for col in selected_columns:  # Iterate original list
        current_filters = allowed_values.copy() if allowed_values else {}
        if col in current_filters:
            del current_filters[col]

        unique_values = analytics_manager.get_unique_column_values(
            workflow_type=workflow_enum,
            column_name=col,
            brain_types=brain_types,
            start_date=start_date,
            end_date=end_date,
            statuses=selected_statuses,
            filter_column_values=current_filters,
        )

        if unique_values:
            current_col_value = allowed_values.get(col)
            value_selectors.append(create_value_selector(col, unique_values, current_col_value))

    if not value_selectors:
        return [], status_options

    return html.Div(value_selectors, style=VALUE_SELECTOR_STYLE), status_options


def _build_allowed_values_per_column(
    selected_columns: list[str] | None, column_values_from_all: list[list[str] | None], column_ids: list[dict]
) -> dict[str, list[str]]:
    """Build column filters dictionary from selected values."""
    if not selected_columns or not column_values_from_all or not column_ids:
        return {}

    values_map = {col_id["column"]: values for values, col_id in zip(column_values_from_all, column_ids)}
    result = {col: values for col in selected_columns if (values := values_map.get(col))}

    return result


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
    brain_types: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    selected_workflows: list[str] | None,
    selected_statuses: list[str] | None,
    selected_columns: list[str] | None,
    column_values: list[list[str] | None],
    column_ids: list[dict],
) -> dict | None:
    """Export filtered workflow data to CSV."""
    if not n_clicks or not selected_workflows:
        return None

    allowed_values_list_dict = _build_allowed_values_per_column(selected_columns, column_values, column_ids)

    is_single_workflow = len(selected_workflows) == 1
    final_statuses = selected_statuses if is_single_workflow else None
    final_allowed_values = allowed_values_list_dict if is_single_workflow else None

    df = analytics_manager.get_workflow_export_data(
        workflows=selected_workflows,
        brain_types=brain_types,
        start_date=start_date,
        end_date=end_date,
        statuses=final_statuses,
        allowed_values_per_column=final_allowed_values,
        limit=100000,
    )

    if df.empty:
        return None

    filename = f"{'_'.join(selected_workflows)}_data_{datetime.now().strftime('%d-%m-%Y')}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)


@callback(
    [
        Output(ExportComponentsIds.EXPORT_PREVIEW_MODAL, "is_open"),
        Output(ExportComponentsIds.EXPORT_PREVIEW_TABLE, "children"),
    ],
    [Input(ExportComponentsIds.EXPORT_PREVIEW_BUTTON, "n_clicks")],
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
)
def toggle_preview_modal(
    preview_clicks: int,
    brain_types: list[str] | None,
    start_date: str | None,
    end_date: str | None,
    selected_workflows: list[str] | None,
    selected_statuses: list[str] | None,
    selected_columns: list[str] | None,
    column_values: list[list[str] | None],
    column_ids: list[dict],
) -> tuple[bool, list[str] | None]:
    """Toggle the preview modal and populate the preview table with the filtered data."""
    ctx = callback_context
    if not ctx.triggered or not preview_clicks or not selected_workflows:
        return False, None

    allowed_values_list_dict = _build_allowed_values_per_column(selected_columns, column_values, column_ids)

    is_single_workflow = len(selected_workflows) == 1
    final_statuses = selected_statuses if is_single_workflow else None
    final_allowed_values = allowed_values_list_dict if is_single_workflow else None

    df = analytics_manager.get_workflow_export_data(
        workflows=selected_workflows,
        brain_types=brain_types,
        start_date=start_date,
        end_date=end_date,
        statuses=final_statuses,
        allowed_values_per_column=final_allowed_values,
        limit=100,
    )

    if df.empty:
        return True, [html.Tr([html.Td("No data found matching the current filters")])]

    header = [html.Thead(html.Tr([html.Th(col) for col in df.columns]))]

    rows = []
    for _, row in df.iterrows():
        rows.append(html.Tr([html.Td(str(row[col])) for col in df.columns]))
    body = [html.Tbody(rows)]

    footer = []
    if len(df) == 100:
        footer = [
            html.Tfoot(html.Tr([html.Td("Showing first 100 rows. Download to see all data.", colSpan=len(df.columns))]))
        ]

    return True, header + body + footer
