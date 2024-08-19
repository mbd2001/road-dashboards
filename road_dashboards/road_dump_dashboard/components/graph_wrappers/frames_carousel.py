import pickle as pkl
import re
from dataclasses import dataclass

import dash_bootstrap_components as dbc
import orjson
from dash import (
    MATCH,
    Input,
    Output,
    Patch,
    State,
    callback,
    callback_context,
    dcc,
    html,
    no_update,
    page_registry,
    set_props,
)
from road_database_toolkit.athena.athena_utils import query_athena
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

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
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.components.logical_components.frame_drawer import draw_img, draw_top_view
from road_dashboards.road_dump_dashboard.components.logical_components.queries_manager import (
    IMG_LIMIT,
    generate_diff_query,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    get_curr_page_tables,
    load_object,
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
    Output({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    Input({"type": GENERIC_SHOW_DIFF_BTN, "index": MATCH}, "n_clicks"),
    Input({"type": GENERIC_FILTER_IGNORES_BTN, "index": MATCH}, "on"),
    State({"type": GENERIC_CONF_EXTRA_INFO, "index": MATCH}, "data-graph"),
    State(MD_FILTERS, "data"),
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
    meta_data_filters,
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
        or main_dump == secondary_dump
        or (
            triggered_id["type"] == GENERIC_FILTER_IGNORES_BTN
            and (not curr_drawn_graph or orjson.loads(curr_drawn_graph)["name"] != triggered_id["index"])
        )
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
    ):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    parsed_properties = load_object(graph_properties)
    query = generate_diff_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        parsed_properties.column_to_compare,
        parsed_properties.extra_columns,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=parsed_properties.ignore_filter if filter_ignores else "",
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, main_dump, secondary_dump
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
    State(MD_FILTERS, "data"),
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
    meta_data_filters,
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
        or main_dump == secondary_dump
        or (
            triggered_id == DYNAMIC_CONF_DROPDOWN
            and (not curr_drawn_graph or orjson.loads(curr_drawn_graph)["name"] != DYNAMIC_CONF_MAT)
        )
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
        or not dynamic_column
    ):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    page_properties = page_registry[f"pages.{pathname.strip('/')}"]
    main_tables = tables[page_properties["main_table"]]
    meta_data_tables = tables.get(page_properties["meta_data_table"])

    graph_properties = {
        "name": DYNAMIC_CONF_MAT,
        "column_to_compare": dynamic_column,
        "extra_columns": [dynamic_column],
        "ignore_filter": "",
    }
    query = generate_diff_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        graph_properties["column_to_compare"],
        graph_properties["extra_columns"],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=graph_properties["ignore_filter"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, main_dump, secondary_dump
    )
    return (
        main_img_figs,
        main_world_figs,
        secondary_img_figs,
        secondary_world_figs,
        0,
        False,
        orjson.dumps(graph_properties),
    )


@callback(
    Output(MAIN_IMG, "children"),
    Output(MAIN_WORLD, "children"),
    Output(SECONDARY_IMG, "children"),
    Output(SECONDARY_WORLD, "children"),
    Output(IMAGES_IND, "data"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    State(URL, "pathname"),
    State(CURR_DRAWN_GRAPH, "data"),
)
def draw_diffs_general_buttons_case(
    meta_data_filters,
    tables,
    population,
    main_dump,
    secondary_dump,
    pathname,
    curr_drawn_graph,
):
    if (
        main_dump == secondary_dump
        or not curr_drawn_graph
        or not population
        or not tables
        or not main_dump
        or not secondary_dump
    ):
        return no_update, no_update, no_update, no_update, no_update

    main_tables, meta_data_tables = get_curr_page_tables(tables, pathname)
    curr_drawn_graph = orjson.loads(curr_drawn_graph)
    query = generate_diff_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        curr_drawn_graph["column_to_compare"],
        curr_drawn_graph["extra_columns"],
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
        extra_filters=curr_drawn_graph["ignore_filter"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = compute_images_from_query_data(
        data, main_dump, secondary_dump
    )
    return main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs, 0


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
    sorted_df = labels_df.sort_values("obj_id")
    labels_dict = {x: y.to_dict("records") for x, y in sorted_df.groupby(["clip_name", "grabindex"])}
    return labels_dict
