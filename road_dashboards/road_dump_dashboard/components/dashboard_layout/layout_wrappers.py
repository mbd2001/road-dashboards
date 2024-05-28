import dash_bootstrap_components as dbc
from dash import dcc


def card_wrapper(object_list, **kwargs):
    return dbc.Card(dbc.CardBody(object_list), className="mt-5", style={"borderRadius": "15px"}, **kwargs)


def loading_wrapper(object_list, **kwargs):
    """A Loading component that wraps any other component list and displays a spinner
    until the wrapped component has rendered."""

    return dcc.Loading(id="loading", type="circle", children=object_list, **kwargs)
