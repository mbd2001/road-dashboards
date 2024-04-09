import base64

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State, no_update
import plotly.graph_objects as go
from road_eval_dashboard.components.components_ids import GRAPH_TO_COPY


def card_wrapper(object_list):
    return dbc.Card([dbc.CardBody(object_list)], className="mt-5", style={"borderRadius": "15px"})


def loading_wrapper(object_list, is_full_screen=False):
    """A Loading component that wraps any other component list and displays a spinner
    until the wrapped component has rendered."""

    return dcc.Loading(id="loading", type="circle", children=object_list, fullscreen=is_full_screen)

def graph_wrapper(graph_id):
    layout = html.Div([loading_wrapper(dcc.Graph(id=graph_id, config={"displayModeBar": False})),
                       dcc.Clipboard(
                           id=f"icon_{graph_id}",
                           title="copy",
                           style={
                               "position": "absolute",
                               "top": 5,
                               "right": 20,
                               "fontSize": 15,
                           },
                       ),
                       dbc.Alert(
            "Copied!",
            id=f"alert_{graph_id}",
            is_open=False,
            fade=True,
            duration=4000,
        ),])

    callback(Output(GRAPH_TO_COPY, "data"),
             Output(f"alert_{graph_id}", "is_open"),
    Input(f"icon_{graph_id}", "n_clicks"),
    State(graph_id, "figure"),
    background=True)(set_copy_store)

    return layout

def set_copy_store(n_clicks, fig_to_copy):
    if not n_clicks:
        return no_update, no_update
    fig_to_copy = go.Figure(fig_to_copy)
    image_bytes_io = fig_to_copy.to_image(format="png", engine="kaleido")
    encoded_image = base64.b64encode(image_bytes_io).decode('utf-8')
    return encoded_image, True