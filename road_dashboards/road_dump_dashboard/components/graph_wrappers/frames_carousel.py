import json
import re
from dataclasses import dataclass

import dash_bootstrap_components as dbc
import numpy as np
from dash import ALL, Input, Output, Patch, State, callback, callback_context, dcc, html, no_update, page_registry
from natsort import natsorted
from road_database_toolkit.athena.athena_utils import query_athena
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    CURR_DRAWN_GRAPH,
    DYNAMIC_CONF_DROPDOWN,
    DYNAMIC_SHOW_DIFF_BTN,
    FRAMES_LAYOUT,
    GENERIC_FILTER_IGNORES_BTN,
    GENERIC_SHOW_DIFF_BTN,
    IMAGES_IND,
    MAIN_IMG,
    MAIN_NET_DROPDOWN,
    MAIN_WORLD,
    MD_FILTERS,
    NEXT_BTN,
    POPULATION_DROPDOWN,
    PREV_BTN,
    SECONDARY_IMG,
    SECONDARY_NET_DROPDOWN,
    SECONDARY_WORLD,
    TABLES,
    URL,
)
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import GRAPHS_PER_PAGE
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.frame_drawer import draw_img, draw_top_view
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import (
    IMG_LIMIT,
    generate_diff_with_labels_query,
)


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
    Output(MAIN_IMG, "children"),
    Output(MAIN_WORLD, "children"),
    Output(SECONDARY_IMG, "children"),
    Output(SECONDARY_WORLD, "children"),
    Output(IMAGES_IND, "data"),
    Output(FRAMES_LAYOUT, "hidden"),
    Output(CURR_DRAWN_GRAPH, "data"),
    Input({"type": GENERIC_FILTER_IGNORES_BTN, "index": ALL}, "on"),
    Input({"type": GENERIC_SHOW_DIFF_BTN, "index": ALL}, "n_clicks"),
    Input(DYNAMIC_SHOW_DIFF_BTN, "n_clicks"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    Input(DYNAMIC_CONF_DROPDOWN, "value"),
    State(URL, "pathname"),
    State(CURR_DRAWN_GRAPH, "data"),
)
def draw_diffs(
    ignore_filters,
    generic_diff_n_clicks,
    dynamic_diff_n_clicks,
    meta_data_filters,
    tables,
    population,
    main_dump,
    secondary_dump,
    dynamic_column,
    pathname,
    curr_drawn_graph,
):
    triggered_id = callback_context.triggered_id
    dynamic_btn_case = triggered_id == DYNAMIC_SHOW_DIFF_BTN
    generic_btn_case = isinstance(triggered_id, dict) and triggered_id["type"] == GENERIC_SHOW_DIFF_BTN
    env_change_case = not dynamic_btn_case and not generic_btn_case
    if (
        main_dump == secondary_dump
        or (env_change_case and not curr_drawn_graph)
        or (dynamic_btn_case and not dynamic_column)
        or (
            isinstance(triggered_id, dict)
            and triggered_id["type"] == GENERIC_FILTER_IGNORES_BTN
            and triggered_id["index"] != curr_drawn_graph
        )
        or (triggered_id == DYNAMIC_CONF_DROPDOWN and curr_drawn_graph != DYNAMIC_SHOW_DIFF_BTN)
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
    ):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    if dynamic_btn_case:
        graph = DYNAMIC_SHOW_DIFF_BTN
    elif generic_btn_case:
        graph = triggered_id["index"]
    else:
        graph = curr_drawn_graph

    page_name = pathname.strip("/")
    if graph == DYNAMIC_SHOW_DIFF_BTN:
        column_to_compare = dynamic_column
        extra_columns = [column_to_compare]
        extra_filters = None
    else:
        ignore_filters = [i for i in callback_context.inputs_list[0] if i["id"]["index"] == graph][0]["value"]
        graph_properties = GRAPHS_PER_PAGE[page_name]["conf_mat_graphs"][graph]
        column_to_compare = graph_properties["column_to_compare"]
        extra_columns = graph_properties["extra_columns"]
        extra_filters = graph_properties["ignore_filter"] if ignore_filters else None

    page_properties = page_registry[f"pages.{page_name}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])
    lables_table = tables[page_properties["main_table"]]
    query = generate_diff_with_labels_query(
        main_dump,
        secondary_dump,
        main_tables,
        lables_table,
        population,
        column_to_compare,
        extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=extra_filters,
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, main_dump, secondary_dump
    )
    return main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs, 0, False, graph


def compute_images_from_query_data(data, main_dump, secondary_dump):
    main_labels_df = split_df_columns_by_start_and_end(data, "main_start", "secondary_start")
    secondary_labels_df = split_df_columns_by_start_and_end(data, "secondary_start")
    main_lables_dict = parse_labels_df(main_labels_df)
    secondary_label_dict = parse_labels_df(secondary_labels_df)

    clip_names, grab_indexes = list(zip(*main_lables_dict.keys()))
    grab_indexes = [int(gi) for gi in grab_indexes]
    data_types = ["data"] * len(clip_names)

    images = DroneViewDBManager.load_multiple_clips_images(clip_names, grab_indexes, data_types)
    main_img_figs = []
    main_world_figs = []
    secondary_img_figs = []
    secondary_world_figs = []
    for clip_name, grab_index in zip(clip_names, grab_indexes):
        curr_img = images[clip_name]["data"][grab_index][0][0]
        main_labels = main_lables_dict[(clip_name, grab_index)]
        secondary_label = secondary_label_dict[(clip_name, grab_index)]
        main_img_figs.append(draw_img(curr_img, main_labels, main_dump, clip_name, grab_index))
        main_world_figs.append(draw_top_view(main_labels))
        secondary_img_figs.append(draw_img(curr_img, secondary_label, secondary_dump, clip_name, grab_index))
        secondary_world_figs.append(draw_top_view(secondary_label))

    return main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs


def split_df_columns_by_start_and_end(df, start_col, end_col=None):
    columns_to_return = []
    is_active = False
    for col in df.columns:
        if col == end_col:
            break
        if is_active:
            columns_to_return.append(col)
            continue
        if col == start_col:
            is_active = True

    return df[columns_to_return]


def parse_labels_df(labels_df):
    if labels_df.empty:
        return {}

    labels_df = labels_df.rename(columns=lambda x: re.sub(r"\.\d+$", "", x))
    labels_df = labels_df[labels_df["obj_id"].notna()]
    labels_dict = {
        x: y.to_dict("records") for x, y in labels_df.sort_values("obj_id").groupby(["clip_name", "grabindex"])
    }
    labels_dict = {
        frame_id: [merge_partitioned_columns(cand) for cand in frame_cands]
        for frame_id, frame_cands in labels_dict.items()
    }
    return labels_dict


def merge_partitioned_columns(labels_dict):
    merged_labels_dict = {}
    for col in natsorted(labels_dict.keys()):
        col_val = labels_dict[col]
        if re.search(r"_\d+$", col) is None:
            merged_labels_dict[col] = col_val
            continue

        if isinstance(col_val, str):
            col_val = json.loads(col_val)
        new_col = re.sub(r"_\d+$", "", col)
        if new_col not in merged_labels_dict:
            merged_labels_dict[new_col] = np.array(col_val)
        else:
            merged_labels_dict[new_col] = np.vstack((merged_labels_dict[new_col], col_val))

    return merged_labels_dict
