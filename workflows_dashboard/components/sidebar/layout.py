import dash_bootstrap_components as dbc
from dash import dcc, html

from workflows_dashboard.config import BRAIN_OPTIONS, BRAIN_SELECTOR, DATE_RANGE_PICKER

from . import callbacks  # DO NOT REMOVE!


def render_sidebar():
    return dbc.Col(
        [
            html.H4("Filters", className="mb-3"),
            html.H6("Brain Selection", className="mb-2"),
            dcc.Dropdown(
                id=BRAIN_SELECTOR,
                options=[{"label": brain_type.upper(), "value": brain_type} for brain_type in BRAIN_OPTIONS],
                value=[BRAIN_OPTIONS[0]],
                multi=True,
                clearable=False,
                className="mb-4",
            ),
            html.Div(
                [
                    html.H6("Date Range", className="mb-2"),
                    dcc.DatePickerRange(
                        id=DATE_RANGE_PICKER,
                        start_date_placeholder_text="Start Date",
                        end_date_placeholder_text="End Date",
                        calendar_orientation="vertical",
                        display_format="DD-MM-YYYY",
                        className="mb-2",
                        style={"width": "100%"},
                    ),
                    dbc.Button("Reset Dates", id="reset-dates-button", color="secondary", size="sm", className="mt-2"),
                ],
                className="mb-4",
            ),
        ],
        width=2,
        className="bg-light p-4",
    )
