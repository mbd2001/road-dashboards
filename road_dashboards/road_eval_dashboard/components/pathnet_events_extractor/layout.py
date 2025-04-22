import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dash_table, dcc, html
from dash_daq import BooleanSwitch

import road_dashboards.road_eval_dashboard.components.pathnet_events_extractor.callbacks  # noqa
from road_dashboards.road_eval_dashboard.components.components_ids import (
    PATHNET_EVENTS_CLIPS_UNIQUE_SWITCH,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DIST_DROPDOWN_DIV,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_EVENTS_ORDER_BY,
    PATHNET_EVENTS_EVENTS_ORDER_BY_DIV,
    PATHNET_EVENTS_EXCLUDE_NONE_SWITCH,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_RE_REF_THRESHOLD,
    PATHNET_EVENTS_RE_SWITCH,
    PATHNET_EVENTS_RE_SWITCH_DIV,
    PATHNET_EVENTS_RE_THRESHOLD,
    PATHNET_EVENTS_RE_THRESHOLDS_DIV,
    PATHNET_EVENTS_REF_DIV,
    PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_REF_NET_ID_DROPDOWN,
    PATHNET_EVENTS_REF_THRESHOLD,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_ROLE_DROPDOWN_DIV,
    PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN,
    PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN_DIV,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EVENTS_THRESHOLD,
    PATHNET_EVENTS_THRESHOLDS_DIV,
    PATHNET_EVENTS_UNIQUE_SWITCH,
    PATHNET_EXPORT_TO_BOOKMARK_BUTTON,
    PATHNET_EXPORT_TO_JUMP_BUTTON,
    PATHNET_EXTRACT_EVENTS_LOG_MESSAGE,
)
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper, loading_wrapper
from road_dashboards.road_eval_dashboard.utils.distances import SECONDS
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list


# ------------------------------------------------- layout-creation ------------------------------------------------- #
def create_header_row():
    return dbc.Row(
        [
            dbc.Col(html.H3("Extract events", className="mb-5"), width=10),
            dbc.Col(
                dbc.Button(
                    "Create Jump",
                    id=PATHNET_EXPORT_TO_JUMP_BUTTON,
                    color="primary",
                    className="me-1",
                    style={"position": "absolute", "top": 5, "right": 90},
                ),
                width=2,
            ),
            dbc.Col(
                dbc.Button(
                    "Export",
                    id=PATHNET_EXPORT_TO_BOOKMARK_BUTTON,
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


def create_net_options_dropdown_row():
    return dbc.Row(
        [
            dbc.Col(loading_wrapper(dcc.Dropdown(id=PATHNET_EVENTS_NET_ID_DROPDOWN, placeholder="Select Net-ID"))),
            dbc.Col(
                loading_wrapper(dcc.Dropdown(id=PATHNET_EVENTS_DP_SOURCE_DROPDOWN, placeholder="Select DP-Source"))
            ),
            dbc.Col(
                daq.BooleanSwitch(
                    id=PATHNET_EVENTS_UNIQUE_SWITCH,
                    on=False,
                    label="Unique events - Compare 2 nets / dp-sources",
                    labelPosition="left",
                    style={"margin-left": "0px", "display": "inline-block"},
                ),
                width=2,
                style={"text-align": "left"},
            ),
        ],
        style={"margin-bottom": "10px"},
    )


def create_ref_net_options_dropdown_row():
    return html.Div(
        id=PATHNET_EVENTS_REF_DIV,
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        loading_wrapper(
                            dcc.Dropdown(id=PATHNET_EVENTS_REF_NET_ID_DROPDOWN, placeholder="Select ref Net-ID")
                        )
                    ),
                    dbc.Col(
                        loading_wrapper(
                            dcc.Dropdown(id=PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN, placeholder="Select ref DP-Source")
                        )
                    ),
                    dbc.Col(width=2),
                ],
                style={"margin-bottom": "10px"},
            )
        ],
        hidden=True,
    )


def create_filtering_dropdowns_row():
    return dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    id=PATHNET_EVENTS_METRIC_DROPDOWN,
                    options=create_dropdown_options_list(labels=["inaccurate", "out-of-lane", "false", "miss", "role"]),
                    placeholder="Select Metric",
                ),
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_ROLE_DROPDOWN_DIV,
                    children=[
                        dcc.Dropdown(
                            id=PATHNET_EVENTS_ROLE_DROPDOWN,
                            options=create_dropdown_options_list(labels=["host", "non-host"]),
                            placeholder="Select Role",
                        )
                    ],
                    hidden=True,
                )
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN_DIV,
                    children=[
                        dcc.Dropdown(
                            id=PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN,
                            options=create_dropdown_options_list(
                                labels=["lane_role", "split_role", "merge_role", "primary_role"]
                            ),
                            placeholder="Select Semantic Role",
                        )
                    ],
                    hidden=True,
                )
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN_DIV,
                    children=[
                        dcc.Dropdown(
                            id=PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN,
                            options=create_dropdown_options_list(
                                labels=["lane_role", "split_role", "merge_role", "primary_role"]
                            ),
                            placeholder="Select Semantic Role",
                        ),
                        BooleanSwitch(
                            id=PATHNET_EVENTS_EXCLUDE_NONE_SWITCH,
                            on=False,
                            label="Exclude None",
                            labelPosition="left",
                            style={"margin-top": "5px"},
                        ),
                    ],
                    hidden=True,
                )
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_DIST_DROPDOWN_DIV,
                    children=[
                        dcc.Dropdown(
                            id=PATHNET_EVENTS_DIST_DROPDOWN,
                            options=create_dropdown_options_list(labels=SECONDS),
                            placeholder="Select Dist (sec)",
                        )
                    ],
                    hidden=True,
                )
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_EVENTS_ORDER_BY_DIV,
                    children=[
                        dcc.Dropdown(
                            id=PATHNET_EVENTS_EVENTS_ORDER_BY,
                            options=create_dropdown_options_list(labels=["ASC", "DESC"]),
                            placeholder="Select Order By",
                        )
                    ],
                    hidden=True,
                )
            ),
            dbc.Col(
                html.Div(
                    id=PATHNET_EVENTS_RE_SWITCH_DIV,
                    children=[
                        daq.BooleanSwitch(
                            id=PATHNET_EVENTS_RE_SWITCH,
                            on=False,
                            label="Road edges only",
                            labelPosition="left",
                            style={"margin-left": "0px", "display": "inline-block"},
                        )
                    ],
                    hidden=True,
                ),
                width=2,
                style={"text-align": "left"},
            ),
        ],
        style={"margin-bottom": "10px"},
    )


def create_unique_thresholds_row(re_thresholds=False):
    return html.Div(
        id=PATHNET_EVENTS_RE_THRESHOLDS_DIV if re_thresholds else PATHNET_EVENTS_THRESHOLDS_DIV,
        children=dbc.Row(
            [
                dbc.Col(
                    dcc.Input(
                        id=PATHNET_EVENTS_RE_THRESHOLD if re_thresholds else PATHNET_EVENTS_THRESHOLD,
                        type="number",
                        style={"width": "inherit", "height": "100%", "appearance": "textfield"},
                    ),
                ),
                dbc.Col(
                    dcc.Input(
                        id=PATHNET_EVENTS_RE_REF_THRESHOLD if re_thresholds else PATHNET_EVENTS_REF_THRESHOLD,
                        type="number",
                        style={"width": "inherit", "height": "100%", "appearance": "textfield"},
                    )
                ),
                dbc.Col(style={"width": "inherit", "height": "100%"}),
            ],
            style={"margin-bottom": "10px"},
        ),
        hidden=True,
    )


def create_submit_events_filtering_row():
    return dbc.Row(
        [
            dbc.Col(dbc.Button("Extract", id=PATHNET_EVENTS_SUBMIT_BUTTON, color="success")),
            dbc.Col(
                daq.BooleanSwitch(
                    id=PATHNET_EVENTS_CLIPS_UNIQUE_SWITCH,
                    on=False,
                    label="Unique clips",
                    labelPosition="left",
                    style={"margin-left": "0px", "display": "inline-block"},
                ),
                width=2,
                style={"text-align": "left"},
            ),
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
        ],
        style={"margin-bottom": "10px"},
    )


def create_events_extractor_layout():
    header_row = create_header_row()

    net_options_dropdowns_row = create_net_options_dropdown_row()

    ref_net_options_dropdowns_row = create_ref_net_options_dropdown_row()

    filtering_dropdowns_row = create_filtering_dropdowns_row()

    submit_events_filtering_row = create_submit_events_filtering_row()

    unique_thresholds_row = create_unique_thresholds_row()

    unique_re_threshold_row = create_unique_thresholds_row(re_thresholds=True)

    log_msg_div = loading_wrapper(html.Div(id=PATHNET_EXTRACT_EVENTS_LOG_MESSAGE))

    events_datatable_div = dash_table.DataTable(id=PATHNET_EVENTS_DATA_TABLE, page_size=20)

    events_extractor = card_wrapper(
        [
            header_row,
            net_options_dropdowns_row,
            ref_net_options_dropdowns_row,
            filtering_dropdowns_row,
            unique_thresholds_row,
            unique_re_threshold_row,
            submit_events_filtering_row,
            log_msg_div,
            events_datatable_div,
        ]
    )
    return events_extractor


layout = create_events_extractor_layout()
