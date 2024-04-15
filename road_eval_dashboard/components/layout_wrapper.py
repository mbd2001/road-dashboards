import base64
from io import BytesIO

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State, no_update, MATCH, ALL, ctx
import plotly.graph_objects as go
from road_eval_dashboard.components.components_ids import GRAPH_TO_COPY
from road_eval_dashboard.utils.jira_handler import get_jira_issues_from_prefix, add_image_in_comment


def card_wrapper(object_list):
    return dbc.Card([dbc.CardBody(object_list)], className="mt-5", style={"borderRadius": "15px"})


def loading_wrapper(object_list, is_full_screen=False):
    """A Loading component that wraps any other component list and displays a spinner
    until the wrapped component has rendered."""

    return dcc.Loading(id="loading", type="circle", children=object_list, fullscreen=is_full_screen)

def graph_wrapper(graph_id):
    TOKENS_TO_REPLACE = ['{',',',':','}',"'", '.']
    graph_id_str = str(graph_id)
    for k in TOKENS_TO_REPLACE:
        graph_id_str = graph_id_str.replace(k,'')
    layout = html.Div(id={"type": "graph_wrapper", "id": graph_id_str}, children=[loading_wrapper(dcc.Graph(id=graph_id, config={"displayModeBar": False})),
                       dcc.Clipboard(
                           id={"type": "copy_button", "id": graph_id_str},
                           title="copy",
                           style={
                               "position": "absolute",
                               "top": 5,
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
                           className="fa-solid fa-download"
                       ),
                      html.Div([
                          dbc.Input(
                              type="text",
                              id={"type": "jira-search", "id": graph_id_str},
                              placeholder="Enter JIRA",
                              persistence=False,
                              autocomplete="off",
                              list=f'{{"id":"{graph_id_str}","type":"jira-search-suggestions"}}',
                              style={
                                "line-height": 1.0,
                                "width": "80%",
                              }
                          ),
                          html.Datalist(
                              id={"type": "jira-search-suggestions", "id": graph_id_str},
                              children=[html.Option(
                                  value='empty')])
                      ],
                          style={
                              "position": "absolute",
                              "top": 5,
                              "right": 45,
                          },
                      ),
                       dcc.Download(id={"type": "download", "id": graph_id_str}),
                       dbc.Alert(
            "Copied!",
            id={"type": "copy_alert", "id": graph_id_str},
            is_open=False,
            fade=True,
            duration=4000,
        ),
          dbc.Alert(
              "Exported To JIRA!",
              id={"type": "jira_alert",
                  "id": graph_id_str},
              is_open=False,
              fade=True,
              duration=4000,
          )
        ,], style={'position': 'relative'})

    return layout

@callback(Output(GRAPH_TO_COPY, "data", allow_duplicate=True),
             Output({"type": "copy_alert", "id": ALL}, "is_open"),
    Input({"type": "copy_button", "id": ALL}, "n_clicks"),
    State({"type": "graph_wrapper", "id": ALL}, "children"),
          State({"type": "copy_alert", "id": ALL}, "is_open"), prevent_initial_call=True)
def set_copy_store(all_n_clicks, all_graph_wrapper_children, all_is_alert_open):
    if all(v is None for v in all_n_clicks):
        return no_update, [no_update for _ in all_n_clicks]
    button_id = ctx.triggered_id
    button_id_index = [i for i in range(len(ctx.inputs_list[0])) if ctx.inputs_list[0][i]['id'] == button_id][0]
    graph_wrapper_children = all_graph_wrapper_children[button_id_index]
    fig_to_copy = graph_wrapper_children[0]['props']['children']['props']['figure']
    fig_to_copy = go.Figure(fig_to_copy)
    image_bytes_io = fig_to_copy.to_image(format="png", engine="kaleido")
    encoded_image = base64.b64encode(image_bytes_io).decode('utf-8')
    all_is_alert_open[button_id_index] = True
    return encoded_image, all_is_alert_open

@callback(Output({"type": "download", "id": MATCH}, "data"),
             Input({"type": "download_button", "id": MATCH}, "n_clicks"),
             State({"type": "graph_wrapper", "id": MATCH}, "children"), prevent_initial_call=True)
def download_plot(n_clicks, graph_wrapper_children):
    fig_to_download = graph_wrapper_children[0]['props']['children']['props']['figure']
    fig_to_download = go.Figure(fig_to_download)
    image_bytes_io = fig_to_download.to_image(format="png", engine="kaleido")
    fig_title = fig_to_download.layout.title.text.strip('<b>').replace(' ','_').lower()
    return dcc.send_bytes(image_bytes_io, filename=f"{fig_title}.png")


@callback(
    Output({"type": "jira-search-suggestions", "id": MATCH}, 'children'),
    Input({"type": "jira-search", "id": MATCH}, "value"),
    prevent_initial_call=True
)
def suggest_jira_tickets(value):
    tickets = get_jira_issues_from_prefix(value)
    if not tickets:
        return [html.Option(value='empty')]
    return [html.Option(value=f"{t.key}-{t.fields.summary}") for t in tickets]

@callback(
    Output({"type": "jira_alert", "id": MATCH}, 'is_open'),
    Input({"type": "jira-search", "id": MATCH}, "n_submit"),
    State({"type": "jira-search", "id": MATCH}, "value"),
    State({"type": "graph_wrapper", "id": MATCH}, "children"),
    prevent_initial_call=True
)
def add_jira_attachment_in_comment(n_submit, value, graph_wrapper_children):
    fig_to_export = graph_wrapper_children[0]['props']['children']['props']['figure']
    fig_to_export = go.Figure(fig_to_export)
    image_bytes_io = fig_to_export.to_image(format="png", engine="kaleido")
    attachment = BytesIO()
    attachment.write(image_bytes_io)
    fig_title = fig_to_export.layout.title.text.strip('<b>').replace(' ', '_').lower()
    value_split = value.split('-')
    issue_key = f"{value_split[0]}-{value_split[1]}" if len(value_split) > 2 else value
    add_image_in_comment(issue_key, image_path=attachment, name=f"{fig_title}.png", comment="Generated By Run Eval Dashboard :)")
    return True