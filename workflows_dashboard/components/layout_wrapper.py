import dash_bootstrap_components as dbc
from dash import dcc, html


def card_wrapper(children):
    return dbc.Card(dbc.CardBody(children), className="mb-4")


def loading_wrapper(children, is_full_screen=False):
    return dcc.Loading(children, type="circle", fullscreen=is_full_screen)
