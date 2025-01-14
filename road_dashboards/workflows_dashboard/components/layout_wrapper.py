import dash_bootstrap_components as dbc
from dash import dcc


def card_wrapper(children):
    return dbc.Card(dbc.CardBody(children), className="mb-4")
