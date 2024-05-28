import time
from io import BytesIO

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import MATCH, Input, Output, State, callback, dcc, html, no_update
from jira import JIRAError

from road_dashboards.road_eval_dashboard.utils.jira_handler import add_image_in_comment, get_jira_issues_from_prefix


def get_jira_modal_layout(graph_id_str):
    return dbc.Modal(
        [
            dbc.ModalHeader("Share To Jira"),
            dbc.ModalBody(
                [
                    dbc.Label("Jira Issue:"),
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
                        children=[html.Option(value="empty")],
                    ),
                    dbc.Label("Jira Comment:", style={"margin-top": 10}),
                    dcc.Textarea(
                        id={"type": "jira-comment", "id": graph_id_str},
                        placeholder="Enter Jira Comment",
                        style={"width": "100%", "height": 200},
                    ),
                    html.Div(id={"type": "jira-modal-error", "id": graph_id_str}, children=[]),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Share", color="primary", id={"type": "jira-share-button", "id": graph_id_str}),
                    dbc.Button("Close", color="secondary", id={"type": "jira-close-button", "id": graph_id_str}),
                ]
            ),
        ],
        id={"type": "jira-share-modal", "id": graph_id_str},
    )


@callback(
    Output({"type": "jira-search-suggestions", "id": MATCH}, "children"),
    Input({"type": "jira-search", "id": MATCH}, "value"),
    prevent_initial_call=True,
)
def suggest_jira_tickets(value):
    tickets = get_jira_issues_from_prefix(value)
    if not tickets:
        return [html.Option(value="empty")]
    return [html.Option(value=f"{t.key}-{t.fields.summary}") for t in tickets]


@callback(
    Output({"type": "jira-share-button", "id": MATCH}, "className", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "color", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "children", allow_duplicate=True),
    Output({"type": "jira-modal-error", "id": MATCH}, "children", allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, "disabled"),
    State({"type": "jira-search", "id": MATCH}, "value"),
    State({"type": "jira-comment", "id": MATCH}, "value"),
    State({"type": "graph_wrapper", "id": MATCH}, "children"),
    prevent_initial_call=True,
)
def add_jira_attachment_in_comment(disabled, jira_issue, jira_comment, graph_wrapper_children):
    if not disabled:
        return no_update, no_update, no_update
    fig_to_export = graph_wrapper_children[0]["props"]["children"]["props"]["figure"]
    fig_to_export = go.Figure(fig_to_export)
    image_bytes_io = fig_to_export.to_image(format="png", engine="kaleido")
    attachment = BytesIO()
    attachment.write(image_bytes_io)
    fig_title = fig_to_export.layout.title.text.strip("<b>").replace(" ", "_").lower()
    value_split = jira_issue.split("-")
    issue_key = f"{value_split[0]}-{value_split[1]}" if len(value_split) > 2 else jira_issue
    try:
        add_image_in_comment(issue_key, image_path=attachment, name=f"{fig_title}.png", comment=jira_comment)
        return "", "success", "Shared!", []
    except JIRAError as je:
        return (
            "",
            "red",
            "Failed!",
            dbc.Label(je.text, style={"margin-top": 10}, color="red"),
        )


@callback(
    Output({"type": "jira-share-modal", "id": MATCH}, "is_open", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "color", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "children", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "disabled", allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, "children"),
    prevent_initial_call=True,
)
def on_jira_share_process_finished(children):
    if children not in ["Failed!", "Shared!"]:
        return no_update, no_update, no_update, no_update
    time.sleep(1)
    return children == "Failed!", "primary", "Share", False


@callback(
    Output({"type": "jira-share-button", "id": MATCH}, "disabled", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "className", allow_duplicate=True),
    Output({"type": "jira-share-button", "id": MATCH}, "children", allow_duplicate=True),
    Input({"type": "jira-share-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def on_jira_share_button_clicked(n_clicks):
    return True, "me-1", dbc.Spinner(size="sm")


@callback(
    Output({"type": "jira-share-modal", "id": MATCH}, "is_open", allow_duplicate=True),
    Input({"type": "jira-modal-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def open_jira_share_modal(n_clicks):
    return True


@callback(
    Output({"type": "jira-share-modal", "id": MATCH}, "is_open", allow_duplicate=True),
    Output({"type": "jira-modal-error", "id": MATCH}, "children", allow_duplicate=True),
    Input({"type": "jira-close-button", "id": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def close_jira_share_modal(n_clicks):
    return False, []


@callback(
    Output({"type": "jira-modal-error", "id": MATCH}, "children", allow_duplicate=True),
    Input({"type": "jira-share-modal", "id": MATCH}, "is_open"),
    prevent_initial_call=True,
)
def close_jira_share_modal_by_background(is_open):
    if is_open:
        return no_update
    return []
