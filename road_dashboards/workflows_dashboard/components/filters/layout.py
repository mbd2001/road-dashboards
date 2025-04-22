import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.common.consts import ComponentIds

from . import callbacks  # noqa
from .brain_selector import render_brain_selector
from .date_range import render_date_range


def render_filters():
    brain_selector = render_brain_selector()
    date_range = render_date_range()
    refresh_btn = dcc.Loading(
        id="loading-refresh",
        type="default",
        children=dbc.Button(
            [html.I(className="fas fa-sync-alt me-2"), "Refresh Data"],
            id=ComponentIds.REFRESH_DB_BUTTON,
            color="primary",
            outline=True,
            className="border-0",
            style={"height": "48px", "minWidth": "100px"},
            title="Refresh Database",
        ),
    )

    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        brain_selector,
                        xs=12,
                        sm=12,
                        md=6,
                        lg="auto",
                        className="d-flex justify-content-center",
                    ),
                    dbc.Col(
                        date_range,
                        xs=12,
                        sm=12,
                        md=6,
                        lg="auto",
                        className="d-flex justify-content-center",
                    ),
                    dbc.Col(
                        refresh_btn,
                        lg="auto",
                        className="d-flex justify-content-end ms-lg-auto",
                    ),
                ],
                className="g-3",
            ),
            className="p-2",
        ),
        className="mb-4 border-0 shadow-sm",
    )
