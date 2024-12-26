import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds


def render_date_range():
    return dbc.Row(  # Main row container
        [
            dbc.Col(
                html.Div(
                    [
                        html.H6(
                            "Date Range",
                            className="text-muted small mb-1 text-center",  # Center headline
                        ),
                        dcc.DatePickerRange(
                            id=ComponentIds.DATE_RANGE_PICKER,
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            display_format="DD-MM-YYYY",
                            className="border-0",
                        ),
                    ],
                    className="d-flex flex-column align-items-center",  # Align content to center
                ),
                width="auto",
            ),
            dbc.Col(
                dbc.Button(
                    [html.I(className="fas fa-undo me-1"), "Reset dates"],
                    id="reset-dates-button",
                    color="light",
                    size="sm",
                    className="ms-2",
                ),
                width="auto",
                className="d-flex align-items-end", 
            ),
        ],
        className="g-0 align-items-end",
    )
