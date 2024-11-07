import dash_bootstrap_components as dbc
from dash import dcc, html

from workflows_dashboard.core_settings.constants import BRAIN_OPTIONS, ComponentIds

from . import callbacks  # DO NOT REMOVE!


def render_sidebar():
    return dbc.Col(
        [
            dbc.Button(
                html.I(className="fas fa-filter"),
                id="toggle-sidebar",
                className="d-lg-none mb-3",
                color="primary",
            ),
            dbc.Collapse(
                [
                    html.H4("Filters", className="mb-3"),
                    html.H6("Brain Selection", className="mb-2"),
                    html.Div(
                        dcc.Dropdown(
                            id=ComponentIds.BRAIN_SELECTOR,
                            options=[
                                {"label": brain_type.upper(), "value": brain_type} for brain_type in BRAIN_OPTIONS
                            ],
                            value=[BRAIN_OPTIONS[0]],
                            multi=True,
                            clearable=False,
                            className="mb-4",
                        ),
                        style={"maxWidth": "100%"},
                    ),
                    html.Div(
                        [
                            html.H6("Date Range", className="mb-2"),
                            dcc.DatePickerRange(
                                id=ComponentIds.DATE_RANGE_PICKER,
                                start_date_placeholder_text="Start Date",
                                end_date_placeholder_text="End Date",
                                calendar_orientation="vertical",
                                display_format="DD-MM-YYYY",
                                className="mb-2",
                                style={"width": "100%"},
                            ),
                            dbc.Button(
                                "Reset Dates", id="reset-dates-button", color="secondary", size="sm", className="mt-2"
                            ),
                        ],
                        className="mb-4",
                    ),
                ],
                id="sidebar-collapse",
                is_open=True,
                className="p-3",
            ),
        ],
        xs=12,
        sm=12,
        md=12,
        lg=2,
        className="pe-lg-4 mb-4 mb-lg-0 position-lg-sticky",
        style={"height": "fit-content", "top": "1rem"},
    )
