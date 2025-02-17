import dash_bootstrap_components as dbc
from dash import dcc, html

from road_dashboards.workflows_dashboard.core_settings.constants import ComponentIds

from . import callbacks  # DO NOT REMOVE!
from .brain_selector import render_brain_selector
from .date_range import render_date_range


def render_filters():
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        render_brain_selector(),
                        xs=12,
                        sm=12,
                        md=6,
                        lg="auto",
                        className="d-flex justify-content-center",
                    ),
                    dbc.Col(
                        render_date_range(),
                        xs=12,
                        sm=12,
                        md=6,
                        lg="auto",
                        className="d-flex justify-content-center",
                    ),
                    dbc.Col(
                        dcc.Loading(
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
                        ),
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
