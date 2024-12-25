import dash_bootstrap_components as dbc
from dash import dcc
from dash.development.base_component import Component


def card_wrapper(object_list: list[Component] | Component, **kwargs) -> Component:
    return dbc.Card(dbc.CardBody(object_list), className="mt-5", style={"borderRadius": "15px"}, **kwargs)


def loading_wrapper(object_list: list[Component] | Component, **kwargs) -> Component:
    """A Loading component that wraps any other component list and displays a spinner
    until the wrapped component has rendered."""

    return dcc.Loading(id="loading", type="circle", children=object_list, **kwargs)
