import base64

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State, no_update, MATCH
import plotly.graph_objects as go
from road_eval_dashboard.components.components_ids import GRAPH_TO_COPY

def card_wrapper(object_list):
    return dbc.Card([dbc.CardBody(object_list)], className="mt-5", style={"borderRadius": "15px"})


def loading_wrapper(object_list, is_full_screen=False):
    """A Loading component that wraps any other component list and displays a spinner
    until the wrapped component has rendered."""

    return dcc.Loading(id="loading", type="circle", children=object_list, fullscreen=is_full_screen)

def graph_wrapper(graph_id):
    graph_wrapper_id = get_wrapper_id(graph_id)
    layout = html.Div([loading_wrapper(dcc.Graph(id=graph_wrapper_id, config={"displayModeBar": False})),
                       dcc.Clipboard(
                           id={**graph_wrapper_id, **{'type': "copy-button"}},
                           title="copy",
                           style={
                               "position": "absolute",
                               "top": 5,
                               "right": 20,
                               "fontSize": 15,
                           },
                       ),
                       dbc.Button(
                           id={**graph_wrapper_id, **{'type': "download-button"}},
                           title="download",
                           style={
                               "position": "absolute",
                               "top": 5,
                               "right": 50,
                               "fontSize": 15,
                           },
                           className="fa-solid fa-download"
                       ),
                       dcc.Download(id={**graph_wrapper_id, **{'type': "download"}}),
                       dbc.Alert(
            "Copied!",
            id={**graph_wrapper_id, **{'type': "copied-alert"}},
            is_open=False,
            fade=True,
            duration=4000,
        ),])

    return layout

@callback(Output(GRAPH_TO_COPY, "data"),
             Output({'graph_wrapper': MATCH, 'type': "copied-alert"}, "is_open", allow_duplicate=True),
    Input({'graph_wrapper': MATCH, 'type': "copy-button"}, "n_clicks"),
    State({'graph_wrapper': MATCH}, "figure"), prevent_initial_call=True)
def set_copy_store(n_clicks, fig_to_copy):
    fig_to_copy = go.Figure(fig_to_copy)
    image_bytes_io = fig_to_copy.to_image(format="png", engine="kaleido")
    encoded_image = base64.b64encode(image_bytes_io).decode('utf-8')
    return encoded_image, True

@callback(Output({'graph_wrapper': MATCH, 'type': "download"}, "data", allow_duplicate=True),
             Input({'graph_wrapper': MATCH, 'type': "download-button"}, "n_clicks"),
             State({'graph_wrapper': MATCH}, "figure"), prevent_initial_call=True)
def download_plot(n_clicks, fig_to_download):
    fig_to_download = go.Figure(fig_to_download)
    image_bytes_io = fig_to_download.to_image(format="png", engine="kaleido")
    fig_title = fig_to_download.layout.title.text.strip('<b>').replace(' ','_').lower()
    return dcc.send_bytes(image_bytes_io, filename=f"{fig_title}.png")

def get_wrapper_id(graph_id):
    if graph_id is not isinstance(graph_id, dict):
        graph_id = {'id': graph_id}
    return {**graph_id, **{'graph_wrapper': graph_id}}
