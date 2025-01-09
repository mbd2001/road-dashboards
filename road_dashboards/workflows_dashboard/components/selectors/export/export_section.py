import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import WORKFLOWS, Status
from road_dashboards.workflows_dashboard.utils.formatting import format_workflow_name

from . import callbacks  # DO NOT REMOVE
from .export_constants import ExportComponentsIds


class WorkflowSelector:
    def render(self):
        return dbc.Col(
            [
                html.Label("Select Workflows", className="form-label"),
                dcc.Dropdown(
                    id=ExportComponentsIds.EXPORT_WORKFLOW_SELECTOR,
                    options=[{"label": format_workflow_name(workflow), "value": workflow} for workflow in WORKFLOWS],
                    value=[WORKFLOWS[0]],
                    multi=True,
                    clearable=False,
                    className="mb-3",
                ),
            ],
            width=12,
        )


class FilterSection:
    def render(self):
        return dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Filter by Status", className="form-label"),
                        dcc.Dropdown(
                            id=ExportComponentsIds.EXPORT_STATUS_SELECTOR,
                            options=[{"label": status.value, "value": status.value} for status in Status],
                            value=None,
                            multi=True,
                            placeholder="Select statuses",
                            className="mb-3",
                        ),
                    ],
                    width=12,
                    lg=6,
                ),
                dbc.Col(
                    [
                        html.Label("Filter by Columns", className="form-label"),
                        dcc.Dropdown(
                            id=ExportComponentsIds.EXPORT_COLUMNS_SELECTOR,
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
                            id=ExportComponentsIds.EXPORT_COLUMN_VALUES_CONTAINER,
                        ),
                    ],
                    width=12,
                ),
            ]
        )


class ExportButton:
    def render(self):
        return dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Preview Data",
                            id=ExportComponentsIds.EXPORT_PREVIEW_BUTTON,
                            color="secondary",
                            className="mt-4 mb-2 me-2",
                            size="lg",
                            style={"width": "10rem", "margin": "0 auto", "display": "inline-block"},
                        ),
                        dbc.Button(
                            "Export Data",
                            id=ExportComponentsIds.EXPORT_BUTTON,
                            color="primary",
                            className="mt-4 mb-2",
                            size="lg",
                            style={"width": "10rem", "margin": "0 auto", "display": "inline-block"},
                        ),
                        dcc.Download(id=ExportComponentsIds.DOWNLOAD_DATAFRAME),

                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Export Data Preview")),
                                dbc.ModalBody(
                                    dbc.Table(
                                        id=ExportComponentsIds.EXPORT_PREVIEW_TABLE,
                                        bordered=True,
                                        hover=True,
                                        responsive=False,
                                        striped=True,

                                    ),
                                    style={
                                        "maxHeight": "80vh", 
                                        "overflowY": "auto",
                                    },                               
                                ),
                            ],
                            id=ExportComponentsIds.EXPORT_PREVIEW_MODAL,
                            size="xl",
                            centered=True,
                            className="mw-100 p-5"

                        ),
                    ],
                    width=12,
                    className="text-center",
                ),
            ]
        )


class ExportSection:
    def render(self):
        return dbc.Col(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("Export Data", className="card-title mb-4"),
                            WorkflowSelector().render(),
                            dbc.Collapse(
                                FilterSection().render(),
                                id=ExportComponentsIds.ADDITIONAL_COLUMNS_CONTAINER,
                                is_open=True,
                            ),
                            ExportButton().render(),
                        ]
                    ),
                    className="shadow-sm",
                ),
            ],
            width=12,
            className="mt-4",
        )
