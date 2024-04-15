import base64
import time
from io import BytesIO

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State, no_update, MATCH, ALL, ctx
import plotly.graph_objects as go
from jira import JIRAError

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
                           className="fa-solid fa-download"
                       ),
                      dbc.Button(
                          id={"type": "jira-modal-button",
                              "id": graph_id_str},
                          title="export to JIRA",
                          style={
                              "position": "absolute",
                              "top": 5,
                              "right": 100,
                              "fontSize": 15,
                          },
                          className="fa-solid fa-share"
                      ),
                      dbc.Modal(
                          [
                              dbc.ModalHeader(
                                  "Share To Jira"),
                              dbc.ModalBody(
                                  [
                                      dbc.Label(
                                          "Jira Issue:"),
                                      dbc.Input(
                                          type="text",
                                          id={"type": "jira-search", "id": graph_id_str},
                                          placeholder="Enter JIRA",
                                          persistence=False,
                                          autocomplete="off",
                                          list=f'{{"id":"{graph_id_str}","type":"jira-search-suggestions"}}',
                                      ),
                                      html.Datalist(
                                          id={"type": "jira-search-suggestions", "id": graph_id_str},
                                          children=[html.Option(
                                              value='empty')]),
                                      dbc.Label("Jira Comment:", style={"margin-top": 10}),
                                      dcc.Textarea(
                                          id={"type": "jira-comment", "id": graph_id_str},
                                          placeholder='Enter Jira Comment',
                                          style={'width': '100%', 'height': 200},
                                      ),
                                      html.Div(id={"type": "jira-modal-error", "id": graph_id_str}, children=[]),
                                  ]
                              ),
                              dbc.ModalFooter(
                                  [
                                      dbc.Button("Share",
                                                 color="primary",
                                                 id={"type": "jira-share-button", "id": graph_id_str}),
                                      dbc.Button(
                                          "Close",
                                          color="secondary",
                                          id={"type": "jira-close-button", "id": graph_id_str}),
                                  ]
                              ),
                          ],
                          id={"type": "jira-share-modal", "id": graph_id_str},
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
    Output({"type": "jira-share-button", "id": MATCH}, 'className', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'color', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'children', allow_duplicate=True),
    Output({"type": "jira-modal-error", "id": MATCH}, 'children', allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, 'disabled'),
    State({"type": "jira-search", "id": MATCH}, "value"),
    State({"type": "jira-comment", "id": MATCH}, "value"),
    State({"type": "graph_wrapper", "id": MATCH}, "children"),
    prevent_initial_call=True
)
def add_jira_attachment_in_comment(disabled, jira_issue, jira_comment, graph_wrapper_children):
    if not disabled:
        return no_update, no_update, no_update
    fig_to_export = graph_wrapper_children[0]['props']['children']['props']['figure']
    fig_to_export = go.Figure(fig_to_export)
    image_bytes_io = fig_to_export.to_image(format="png", engine="kaleido")
    attachment = BytesIO()
    attachment.write(image_bytes_io)
    fig_title = fig_to_export.layout.title.text.strip('<b>').replace(' ', '_').lower()
    value_split = jira_issue.split('-')
    issue_key = f"{value_split[0]}-{value_split[1]}" if len(value_split) > 2 else jira_issue
    try:
        add_image_in_comment(issue_key, image_path=attachment, name=f"{fig_title}.png", comment=jira_comment)
        return '', 'success', "Shared!", []
    except JIRAError as je:
        return '', 'red', "Failed!", dbc.Label(je.text, style={"margin-top": 10}, color='red'),

@callback(
Output({"type": "jira-share-modal", "id": MATCH}, 'is_open', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'color', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'children', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'disabled', allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, 'children'),
    prevent_initial_call=True
)
def on_jira_share_process_finished(children):
    if children not in ["Failed!", "Shared!"]:
        return no_update, no_update, no_update, no_update
    time.sleep(1)
    return children == "Failed!", 'primary', 'Share', False

@callback(
    Output({"type": "jira-share-button", "id": MATCH}, 'disabled', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'className', allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, 'children', allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True
)
def on_jira_share_button_clicked(n_clicks):
    return True, "me-1", dbc.Spinner(size="sm")

@callback(
    Output({"type": "jira-share-modal", "id": MATCH}, 'is_open', allow_duplicate=True),
    Input({"type": "jira-modal-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True
)
def open_jira_share_modal(n_clicks):
    return True

@callback(
    Output({"type": "jira-share-modal", "id": MATCH}, 'is_open', allow_duplicate=True),
    Output({"type": "jira-modal-error", "id": MATCH}, 'children', allow_duplicate=True),
    Input({"type": "jira-close-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True
)
def close_jira_share_modal(n_clicks):
    return False, []

@callback(
    Output({"type": "jira-modal-error", "id": MATCH}, 'children', allow_duplicate=True),
    Input({"type": "jira-share-modal", "id": MATCH}, 'is_open'),
    prevent_initial_call=True
)
def close_jira_share_modal_by_background(is_open):
    if is_open:
        return no_update
    return []