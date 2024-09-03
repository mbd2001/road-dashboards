from typing import List

import dash_bootstrap_components as dbc
from dash import Input, Output, Patch, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DISPLAY_CONF_MATS,
    MAIN_NET_DROPDOWN,
    MAIN_TABLES,
    SECONDARY_NET_DROPDOWN,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper

# from road_dashboards.road_dump_dashboard.components.graph_wrappers import frames_carousel
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_generator import grid_layout
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import Table, load_object


def layout(graphs_properties):
    matrices_layout = html.Div(
        id=DISPLAY_CONF_MATS,
        children=[
            card_wrapper(
                [
                    nets_selection_layout(),
                    grid_layout(graphs_properties),
                ]
            ),
            # frames_carousel.layout(),
        ],
        style={"display": "none"},
    )
    return matrices_layout


def nets_selection_layout():
    nets_selection = dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    id=MAIN_NET_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="----",
                    value="",
                )
            ),
            dbc.Col(
                dcc.Dropdown(
                    id=SECONDARY_NET_DROPDOWN,
                    style={"minWidth": "100%"},
                    multi=False,
                    placeholder="----",
                    value="",
                )
            ),
        ]
    )

    return nets_selection


@callback(
    Output(DISPLAY_CONF_MATS, "style"),
    Input(MAIN_TABLES, "data"),
)
def init_dumps_dropdown(main_tables):
    if not main_tables:
        return no_update

    main_tables: List[Table] = load_object(main_tables).tables
    if len(main_tables) < 2:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "block"
    return patched_style


@callback(
    Output(MAIN_NET_DROPDOWN, "options"),
    Output(MAIN_NET_DROPDOWN, "label"),
    Output(MAIN_NET_DROPDOWN, "value"),
    Input(MAIN_TABLES, "data"),
)
def init_dumps_dropdown(main_tables):
    if not main_tables:
        return no_update, no_update, no_update

    main_tables: List[Table] = load_object(main_tables).tables
    options = {table.dataset_name: table.dataset_name.title() for table in main_tables}
    return options, main_tables[0].dataset_name.title(), main_tables[0].dataset_name


@callback(
    Output(SECONDARY_NET_DROPDOWN, "options"),
    Output(SECONDARY_NET_DROPDOWN, "label"),
    Output(SECONDARY_NET_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "options"),
)
def init_dumps_dropdown(selected_val, options):
    if not selected_val:
        return no_update

    options = {val: title for val, title in options.items() if val != selected_val}
    if not options:
        return no_update, no_update, no_update

    val, title = next(iter(options.items()))
    return options, title, val
