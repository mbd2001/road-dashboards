import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

import road_eval_dashboard.components.pathnet_events_extractor.callbacks
from road_eval_dashboard.components.components_ids import (
    PATHNET_BOOKMARKS_JSON_FILE_NAME,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_ERROR_MESSAGE,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_ORDER_DROPDOWN,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EXPORT_JSON_BUTTON,
    PATHNET_EXPORT_JSON_LOG_MESSAGE,
    PATHNET_EXPORT_TO_BOOKMARK_WINDOW,
    PATHNET_OPEN_EXPORT_EVENTS_WINDOW_BUTTON,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_eval_dashboard.components.queries_manager import distances
from road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list


# ------------------------------------------------- layout-creation ------------------------------------------------- #
def create_events_extractor_layout():
    header_row = dbc.Row(
        [
            dbc.Col(html.H2("Extract events", className="mb-5"), width=10),
            dbc.Col(
                dbc.Button(
                    "Export",
                    id=PATHNET_OPEN_EXPORT_EVENTS_WINDOW_BUTTON,
                    color="primary",
                    className="me-1",
                    style={"position": "absolute", "top": 5, "right": 5},
                ),
                width=2,
                align="end",
            ),
        ],
        style={"position": "relative"},
        justify="between",  # This will spread the columns to the full available width
    )

    export_to_bookmark_window = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Export events to bookmarks")),
            dbc.ModalBody(
                [
                    dbc.Textarea(
                        id=PATHNET_BOOKMARKS_JSON_FILE_NAME,
                        placeholder="Specify a path for saving the events...",
                        style={"width": "100%", "height": "100px"},
                    ),
                    html.Div(id=PATHNET_EXPORT_JSON_LOG_MESSAGE, children=[]),
                ]
            ),
            dbc.ModalFooter(dbc.Button("Export", id=PATHNET_EXPORT_JSON_BUTTON, className="ms-auto", color="primary")),
        ],
        id=PATHNET_EXPORT_TO_BOOKMARK_WINDOW,
        is_open=False,
    )

    net_options_dropdowns_row = dbc.Row(
        [
            dbc.Col(loading_wrapper(dcc.Dropdown(id=PATHNET_EVENTS_NET_ID_DROPDOWN, placeholder="Select Net-ID"))),
            dbc.Col(
                loading_wrapper(dcc.Dropdown(id=PATHNET_EVENTS_DP_SOURCE_DROPDOWN, placeholder="Select DP-Source"))
            ),
        ],
        style={"margin-bottom": "10px"},
    )

    filtering_dropdowns_row = dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_EVENTS_ROLE_DROPDOWN,
                    options=create_dropdown_options_list(labels=["host", "non-host"]),
                    placeholder="Select Role",
                )
            ),
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_EVENTS_DIST_DROPDOWN,
                    options=create_dropdown_options_list(labels=distances),
                    placeholder="Select Dist (sec)",
                ),
            ),
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_EVENTS_METRIC_DROPDOWN,
                    options=create_dropdown_options_list(labels=["accuracy", "false", "miss"]),
                    placeholder="Select Metric",
                ),
            ),
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_EVENTS_ORDER_DROPDOWN,
                    options=create_dropdown_options_list(labels=["Ascending", "Descending"], values=["ASC", "DESC"]),
                    placeholder="Select Order",
                ),
            ),
        ],
        style={"margin-bottom": "10px"},
    )

    submit_events_filtering_row = dbc.Row(
        [
            dbc.Col(dbc.Button("Submit", id=PATHNET_EVENTS_SUBMIT_BUTTON, color="success")),
            dbc.Col(
                dcc.Input(
                    id=PATHNET_EVENTS_NUM_EVENTS,
                    placeholder="Specify number of events to extract (optional)...",
                    min=100,
                    max=150000,
                    step=1,
                    type="number",
                    style={"width": "inherit", "height": "100%"},
                ),
                style={"flex": 15},
            ),
            dbc.Col(html.Div(id=PATHNET_EVENTS_ERROR_MESSAGE), style={"flex": 20}),
        ],
        style={"margin-bottom": "10px"},
    )

    events_extractor = card_wrapper(
        [
            header_row,
            export_to_bookmark_window,
            net_options_dropdowns_row,
            filtering_dropdowns_row,
            submit_events_filtering_row,
            dash_table.DataTable(id=PATHNET_EVENTS_DATA_TABLE, page_size=40),
        ]
    )
    return events_extractor


layout = create_events_extractor_layout()
