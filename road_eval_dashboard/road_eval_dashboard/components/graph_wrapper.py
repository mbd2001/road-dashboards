import base64

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, MATCH, Input, Output, State, callback, ctx, dcc, html, no_update

from road_eval_dashboard.components.components_ids import GRAPH_TO_COPY
from road_eval_dashboard.components.export_jira_modal import get_jira_modal_layout
from road_eval_dashboard.components.layout_wrapper import loading_wrapper


def graph_wrapper(graph_id):
    graph_id_str = get_str_id(graph_id)
    layout = html.Div(
        id={"type": "graph_wrapper", "id": graph_id_str},
        children=[
            loading_wrapper(dcc.Graph(id=graph_id, config={"displayModeBar": False})),
            dcc.Clipboard(
                id={"type": "copy_button", "id": graph_id_str},
                title="copy",
                style={
                    "position": "absolute",
                    "top": 8,
                    "right": 20,
                    "fontSize": 15,
                },
            ),
            dbc.Button(
                id={"type": "download_button", "id": graph_id_str},
                title="download",
                style={
                    "position": "absolute",
                    "top": 5,
                    "right": 50,
                    "fontSize": 15,
                },
                className="fa-solid fa-download",
            ),
            dbc.Button(
                id={"type": "jira-modal-button", "id": graph_id_str},
                title="export to JIRA",
                style={
                    "position": "absolute",
                    "top": 5,
                    "right": 100,
                    "fontSize": 15,
                },
                className="fa-solid fa-share",
            ),
            get_jira_modal_layout(graph_id_str),
            dcc.Download(id={"type": "download", "id": graph_id_str}),
            dbc.Alert(
                "Copied!",
                id={"type": "copy_alert", "id": graph_id_str},
                is_open=False,
                fade=True,
                duration=4000,
            ),
        ],
        style={"position": "relative"},
    )

    return layout


def get_str_id(graph_id):
    TOKENS_TO_REPLACE = ["{", ",", ":", "}", "'", "."]
    graph_id_str = str(graph_id)
    for k in TOKENS_TO_REPLACE:
        graph_id_str = graph_id_str.replace(k, "")
    return graph_id_str


@callback(
    Output(GRAPH_TO_COPY, "data", allow_duplicate=True),
    Output({"type": "copy_alert", "id": ALL}, "is_open"),
    Input({"type": "copy_button", "id": ALL}, "n_clicks"),
    State({"type": "graph_wrapper", "id": ALL}, "children"),
    State({"type": "copy_alert", "id": ALL}, "is_open"),
    prevent_initial_call=True,
)
def copy_graph_image_to_store(all_n_clicks, all_graph_wrapper_children, all_is_alert_open):
    if all(v is None for v in all_n_clicks):
        return no_update, [no_update for _ in all_n_clicks]
    button_id = ctx.triggered_id
    button_id_index = [i for i in range(len(ctx.inputs_list[0])) if ctx.inputs_list[0][i]["id"] == button_id][0]
    graph_wrapper_children = all_graph_wrapper_children[button_id_index]
    fig_to_copy = graph_wrapper_children[0]["props"]["children"]["props"]["figure"]
    fig_to_copy = go.Figure(fig_to_copy)
    image_bytes_io = fig_to_copy.to_image(format="png", engine="kaleido")
    encoded_image = base64.b64encode(image_bytes_io).decode("utf-8")
    all_is_alert_open[button_id_index] = True
    return encoded_image, all_is_alert_open


@callback(
    Output({"type": "download", "id": MATCH}, "data"),
    Input({"type": "download_button", "id": MATCH}, "n_clicks"),
    State({"type": "graph_wrapper", "id": MATCH}, "children"),
    prevent_initial_call=True,
)
def download_plot(n_clicks, graph_wrapper_children):
    fig_to_download = graph_wrapper_children[0]["props"]["children"]["props"]["figure"]
    fig_to_download = go.Figure(fig_to_download)
    image_bytes_io = fig_to_download.to_image(format="png", engine="kaleido")
    fig_title = fig_to_download.layout.title.text.strip("<b>").replace(" ", "_").lower()
    return dcc.send_bytes(image_bytes_io, filename=f"{fig_title}.png")
