import dash_bootstrap_components as dbc

from .brain_selector import render_brain_selector
from .date_range import render_date_range
from . import callbacks  # DO NOT REMOVE!


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
                ],
                className="g-3 justify-content-center",
            ),
            className="p-2",
        ),
        className="mb-4 border-0 shadow-sm",
    ) 