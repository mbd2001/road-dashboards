import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, ComponentIds, Status
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name

from . import callbacks  # DO NOT REMOVE


def create_export_section():
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Export Data", className="card-title mb-4"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Select Workflows", className="form-label"),
                                        dcc.Dropdown(
                                            id=ComponentIds.EXPORT_WORKFLOW_SELECTOR,
                                            options=[
                                                {"label": format_workflow_name(workflow), "value": workflow}
                                                for workflow in WORKFLOWS
                                            ],
                                            value=[WORKFLOWS[0]],
                                            multi=True,
                                            clearable=False,
                                            className="mb-3",
                                        ),
                                    ],
                                    width=12,
                                ),
                            ]
                        ),
                        dbc.Collapse(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Filter by Status", className="form-label"),
                                            dcc.Dropdown(
                                                id=ComponentIds.EXPORT_STATUS_SELECTOR,
                                                options=[
                                                    {"label": status.value, "value": status.value} for status in Status
                                                ],
                                                value=None,
                                                multi=True,
                                                placeholder="Select statuses",
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                        lg=6,
                                    ),
                                    # Columns filter column
                                    dbc.Col(
                                        [
                                            html.Label("Filter by Columns", className="form-label"),
                                            dcc.Dropdown(
                                                id=ComponentIds.EXPORT_COLUMNS_SELECTOR,
                                                options=[],
                                                value=[],
                                                multi=True,
                                                placeholder="Select columns",
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                        lg=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                id=ComponentIds.EXPORT_COLUMN_VALUES_CONTAINER,
                                                className="value-selectors-container",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            id=ComponentIds.ADDITIONAL_COLUMNS_CONTAINER,
                            is_open=True,
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Export Data",
                                            id=ComponentIds.EXPORT_BUTTON,
                                            color="primary",
                                            className="mt-4 mb-2",
                                            size="lg",
                                            style={"width": "10rem", "margin": "0 auto", "display": "block"},
                                        ),
                                        dcc.Download(id=ComponentIds.DOWNLOAD_DATAFRAME),
                                    ],
                                    width=12,
                                ),
                            ]
                        ),
                    ]
                ),
                className="shadow-sm",
            ),
        ],
        width=12,
        className="mt-4",
    )
