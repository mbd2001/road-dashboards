from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import numpy as np
import orjson
import pandas as pd
from dash import MATCH, Input, Output, Patch, State, callback, callback_context, dcc, html, no_update, set_props
from road_database_toolkit.athena.athena_utils import query_athena
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    CURR_DRAWN_GRAPH,
    DYNAMIC_CONF_DROPDOWN,
    DYNAMIC_CONF_MAT,
    DYNAMIC_SHOW_DIFF_BTN,
    FRAMES_LAYOUT,
    GENERIC_CONF_EXTRA_INFO,
    GENERIC_FILTER_IGNORES_BTN,
    GENERIC_SHOW_DIFF_BTN,
    IMAGES_IND,
    MAIN_IMG,
    MAIN_NET_DROPDOWN,
    MAIN_WORLD,
    NEXT_BTN,
    PAGE_FILTERS,
    POPULATION_DROPDOWN,
    PREV_BTN,
    SECONDARY_IMG,
    SECONDARY_NET_DROPDOWN,
    SECONDARY_WORLD,
    URL,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, ConfMatQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.graphs_properties import Graph
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import (
    IMG_LIMIT,
    generate_diff_labels_query,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    dump_object,
    get_existing_column,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.frame_drawer import draw_img, draw_top_view

exclude_columns = ["clip_name", "grabindex", "dump_name"]


@dataclass
class Images:
    main_img_figs: list
    main_world_figs: list
    secondary_img_figs: list
    secondary_world_figs: list
    column_to_compare: str


def layout():
    frames_layout = html.Div(
        id=FRAMES_LAYOUT,
        children=[
            card_wrapper(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                loading_wrapper(html.Div(dcc.Graph(config={"displayModeBar": False}), id=MAIN_WORLD)),
                                width=1,
                            ),
                            dbc.Col(
                                loading_wrapper(html.Div(dcc.Graph(config={"displayModeBar": False}), id=MAIN_IMG)),
                                width=5,
                            ),
                            dbc.Col(
                                loading_wrapper(
                                    html.Div(dcc.Graph(config={"displayModeBar": False}), id=SECONDARY_IMG)
                                ),
                                width=5,
                            ),
                            dbc.Col(
                                loading_wrapper(
                                    html.Div(dcc.Graph(config={"displayModeBar": False}), id=SECONDARY_WORLD)
                                ),
                                width=1,
                            ),
                        ],
                    ),
                    dbc.Row(
                        dbc.Stack(
                            [
                                dbc.Button(
                                    "Prev Frame",
                                    id=PREV_BTN,
                                    className="bg-primary mt-5",
                                    color="secondary",
                                    style={"margin": "10px"},
                                ),
                                dbc.Button(
                                    "Next Frame",
                                    id=NEXT_BTN,
                                    className="bg-primary mt-5",
                                    color="secondary",
                                    style={"margin": "10px"},
                                ),
                            ],
                            direction="horizontal",
                            gap=1,
                        )
                    ),
                ]
            )
        ],
        hidden=True,
    )
    return frames_layout


@callback(
    Output(MAIN_IMG, "children", allow_duplicate=True),
    Output(MAIN_WORLD, "children", allow_duplicate=True),
    Output(SECONDARY_IMG, "children", allow_duplicate=True),
    Output(SECONDARY_WORLD, "children", allow_duplicate=True),
    Output(IMAGES_IND, "data", allow_duplicate=True),
    Input(IMAGES_IND, "data"),
    Input(PREV_BTN, "n_clicks"),
    Input(NEXT_BTN, "n_clicks"),
    prevent_initial_call=True,
)
def update_frame_graphs(
    ind,
    prev_n_clicks,
    next_n_clicks,
):
    triggered_id = callback_context.triggered_id
    if not triggered_id or ind is None:
        return no_update, no_update, no_update, no_update, no_update

    main_img = Patch()
    main_world = Patch()
    secondary_img = Patch()
    secondary_world = Patch()
    if triggered_id != IMAGES_IND:
        n_clicks = callback_context.triggered[0]["value"]
        if n_clicks == 0:
            return no_update, no_update, no_update, no_update, no_update

        main_img[ind]["props"]["style"]["display"] = "none"
        main_world[ind]["props"]["style"]["display"] = "none"
        secondary_img[ind]["props"]["style"]["display"] = "none"
        secondary_world[ind]["props"]["style"]["display"] = "none"

        if triggered_id == PREV_BTN:
            ind = (ind - 1) % IMG_LIMIT
        elif triggered_id == NEXT_BTN:
            ind = (ind + 1) % IMG_LIMIT

    main_img[ind]["props"]["style"]["display"] = "block"
    main_world[ind]["props"]["style"]["display"] = "block"
    secondary_img[ind]["props"]["style"]["display"] = "block"
    secondary_world[ind]["props"]["style"]["display"] = "block"
    return main_img, main_world, secondary_img, secondary_world, ind if triggered_id != IMAGES_IND else no_update


@callback(
    Output({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    Input({"type": GENERIC_SHOW_DIFF_BTN, "index": MATCH}, "n_clicks"),
    Input({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    State({"type": GENERIC_CONF_EXTRA_INFO, "index": MATCH}, "data-graph"),
    State(PAGE_FILTERS, "data"),
    State(TABLES, "data"),
    State(POPULATION_DROPDOWN, "value"),
    State(MAIN_NET_DROPDOWN, "value"),
    State(SECONDARY_NET_DROPDOWN, "value"),
    State(URL, "pathname"),
    State(CURR_DRAWN_GRAPH, "data"),
    prevent_initial_call=True,
)
def draw_diffs_generic_case(
    show_diff_n_clicks,
    filter_ignores,
    graph_properties,
    filters,
    tables,
    population,
    main_dump,
    secondary_dump,
    pathname,
    curr_drawn_graph,
):
    triggered_id = callback_context.triggered_id
    if (
        not show_diff_n_clicks
        or (
            triggered_id["type"] == GENERIC_FILTER_IGNORES_BTN
            and (not curr_drawn_graph or load_object(curr_drawn_graph).name != triggered_id["index"])
        )
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
    ):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    extra_columns = main_tables.get_column_names(exclude_columns=exclude_columns)
    parsed_properties = load_object(graph_properties)
    query = generate_diff_labels_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        parsed_properties.column_to_compare,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=filters,
        extra_filters=parsed_properties.ignore_filter if filter_ignores else "",
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, extra_columns
    )

    set_props(MAIN_IMG, {"children": main_img_figs})
    set_props(MAIN_WORLD, {"children": main_world_figs})
    set_props(SECONDARY_IMG, {"children": secondary_img_figs})
    set_props(SECONDARY_WORLD, {"children": secondary_world_figs})
    set_props(IMAGES_IND, {"data": 0})
    set_props(FRAMES_LAYOUT, {"hidden": False})
    set_props(CURR_DRAWN_GRAPH, {"data": graph_properties})
    return filter_ignores


@callback(
    Output(MAIN_IMG, "children", allow_duplicate=True),
    Output(MAIN_WORLD, "children", allow_duplicate=True),
    Output(SECONDARY_IMG, "children", allow_duplicate=True),
    Output(SECONDARY_WORLD, "children", allow_duplicate=True),
    Output(IMAGES_IND, "data", allow_duplicate=True),
    Output(FRAMES_LAYOUT, "hidden"),
    Output(CURR_DRAWN_GRAPH, "data"),
    State(PAGE_FILTERS, "data"),
    State(TABLES, "data"),
    State(POPULATION_DROPDOWN, "value"),
    State(MAIN_NET_DROPDOWN, "value"),
    State(SECONDARY_NET_DROPDOWN, "value"),
    Input(DYNAMIC_CONF_DROPDOWN, "value"),
    Input(DYNAMIC_SHOW_DIFF_BTN, "n_clicks"),
    State(URL, "pathname"),
    State(CURR_DRAWN_GRAPH, "data"),
    prevent_initial_call=True,
)
def draw_diffs_dynamic_case(
    filters,
    tables,
    population,
    main_dump,
    secondary_dump,
    dynamic_column,
    show_diff_n_clicks,
    pathname,
    curr_drawn_graph,
):
    triggered_id = callback_context.triggered_id
    if (
        not show_diff_n_clicks
        or (
            triggered_id == DYNAMIC_CONF_DROPDOWN
            and (not curr_drawn_graph or load_object(curr_drawn_graph).name != DYNAMIC_CONF_MAT)
        )
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
        or not dynamic_column
    ):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    extra_columns = main_tables.get_column_names(exclude_columns=exclude_columns)
    dynamic_column = get_existing_column(dynamic_column, main_tables, meta_data_tables)
    graph_properties = Graph(
        name=DYNAMIC_CONF_MAT,
        query=ConfMatQuery(
            column_to_compare=Column(dynamic_column),
            main_data_query=BaseDataQuery(
                main_tables=main_tables, meta_data_tables=meta_data_tables, extra_columns=[dynamic_column]
            ),
            secondary_data_query=BaseDataQuery(
                main_tables=main_tables, meta_data_tables=meta_data_tables, extra_columns=[dynamic_column]
            ),
        ),
    )
    query = generate_diff_labels_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        graph_properties.column_to_compare,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=filters,
        extra_filters=graph_properties.ignore_filter,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, extra_columns
    )
    return (
        main_img_figs,
        main_world_figs,
        secondary_img_figs,
        secondary_world_figs,
        0,
        False,
        dump_object(graph_properties),
    )


@callback(
    Output(MAIN_IMG, "children"),
    Output(MAIN_WORLD, "children"),
    Output(SECONDARY_IMG, "children"),
    Output(SECONDARY_WORLD, "children"),
    Output(IMAGES_IND, "data"),
    Input(PAGE_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    State(URL, "pathname"),
    State(CURR_DRAWN_GRAPH, "data"),
)
def draw_diffs_general_buttons_case(
    filters,
    tables,
    population,
    main_dump,
    secondary_dump,
    pathname,
    curr_drawn_graph,
):
    if not curr_drawn_graph or not population or not tables or not main_dump or not secondary_dump:
        return no_update, no_update, no_update, no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    extra_columns = main_tables.get_column_names(exclude_columns=exclude_columns)
    curr_drawn_graph = load_object(curr_drawn_graph)
    query = generate_diff_labels_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        curr_drawn_graph.column_to_compare,
        curr_drawn_graph.extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=filters,
        extra_filters=curr_drawn_graph.ignore_filter,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, extra_columns
    )
    return main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs, 0


def compute_images_from_query_data(data, extra_columns):
    labels_df = parse_labels_df(data, extra_columns)
    dumps_df_list = [d for _, d in labels_df.groupby(["dump_name"])]

    clip_names = dumps_df_list[0].clip_name
    grab_indexes = [int(gi) for gi in dumps_df_list[0].grabindex]
    data_types = ["data"] * len(clip_names)

    images = DroneViewDBManager.load_multiple_clips_images(clip_names, grab_indexes, data_types)
    img_figs = [[]] * len(dumps_df_list)
    world_figs = [[]] * len(dumps_df_list)
    for dump_df, img_fig, world_fig in zip(dumps_df_list, img_figs, world_figs):
        for ind, row in dump_df.iterrows():
            candidates = [{col: row[col][i] for col in row.drop(exclude_columns).index} for i in range(row.obj_id.size)]
            curr_img = images[row.clip_name]["data"][row.grabindex][0][0]
            img_fig.append(draw_img(curr_img, candidates, row.dump_name, row.clip_name, row.grabindex))
            world_fig.append(draw_top_view(candidates))

    return img_figs[0], world_figs[0], img_figs[1], world_figs[1]


def parse_labels_df(labels_df: pd.DataFrame, extra_columns: List[Column]):
    if labels_df.empty:
        return {}

    arr_columns = [col.name for col in extra_columns]
    labels_df[arr_columns] = labels_df[arr_columns].map(safe_json).map(np.array)
    return labels_df


def safe_json(x):
    try:
        return orjson.loads(x)
    except orjson.JSONDecodeError:
        return [x.strip(" ") for x in x.strip("[]").split(",")]
