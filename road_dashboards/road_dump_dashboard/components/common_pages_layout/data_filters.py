from dataclasses import dataclass
from typing import List

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, Patch, State, callback, callback_context, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BoolColumn, Column, StringColumn
from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    ADD_FILTER_BTN,
    ADD_SUB_GROUP,
    FILTER_GROUP,
    FILTER_LIST,
    FILTER_ROW,
    FILTERS,
    MAIN_TABLES,
    MD_COLUMNS,
    MD_OPERATION,
    MD_TABLES,
    MD_VAL,
    MD_VAL_COL,
    OUT_TO_JUMP_BTN,
    REMOVE_SUB_GROUP,
    SHOW_N_FRAMES_BTN,
    UPDATE_FILTERS_BTN,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    TableType,
    get_columns_dict,
    get_existing_column,
    load_object,
)

MAX_FILTERS_PER_GROUP = 10


@dataclass
class Filter:
    column: Column
    # TODO: do stuff with it


class And:
    def __init__(self, filters: List[Filter], *args: Filter):
        pass

    # TODO: do stuff with it


def get_filter_row_initial_layout(index, md_columns_options):
    single_filter_initial_layout = dbc.Row(
        id={"type": FILTER_ROW, "index": index},
        children=[
            dbc.Col(
                children=dcc.Dropdown(
                    id={"type": MD_COLUMNS, "index": index},
                    style={"minWidth": "100%"},
                    multi=False,
                    clearable=True,
                    placeholder="Attribute",
                    value="",
                    options=md_columns_options or [],
                ),
            ),
            dbc.Col(
                children=dcc.Dropdown(
                    id={"type": MD_OPERATION, "index": index},
                    style={"minWidth": "100%"},
                    multi=False,
                    clearable=True,
                    placeholder="----",
                    value="",
                ),
            ),
            dbc.Col(
                id={"type": MD_VAL_COL, "index": index},
                children=dcc.Input(
                    id={"type": MD_VAL, "index": index},
                    style={"minWidth": "100%", "display": "block"},
                    placeholder="----",
                    value="",
                    type="text",
                ),
            ),
            dbc.Col(
                dbc.Button(className=f"fas fa-x", id={"type": "remove_filter_btn", "index": index}, color="secondary"),
                width=1,
            ),
        ],
        style={"margin": "10px"},
    )
    return single_filter_initial_layout


def get_group_layout(index, md_columns_options):
    group_layout = dbc.Row(
        id={"type": FILTER_GROUP, "index": index},
        children=[
            dbc.Stack(
                children=[
                    daq.BooleanSwitch(
                        on=False,
                        label="And <-> Or",
                        labelPosition="top",
                    ),
                    dbc.Button(
                        className=f"ms-auto fas fa-plus",
                        id={"type": ADD_FILTER_BTN, "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                    dbc.Button(
                        className=f"fas fa-link",
                        id={"type": ADD_SUB_GROUP, "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                    dbc.Button(
                        className=f"fas fa-trash",
                        id={"type": REMOVE_SUB_GROUP, "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                ],
                direction="horizontal",
                gap=1,
            ),
            html.Div(
                id={"type": FILTER_LIST, "index": index},
                children=[get_filter_row_initial_layout(index * MAX_FILTERS_PER_GROUP, md_columns_options)],
            ),
        ],
        style={"border": "2px lightskyblue solid", "border-radius": "20px", "margin": "20px"},
    )
    return group_layout


layout = html.Div(
    card_wrapper(
        [
            html.H3("Filters"),
            html.Div(id=FILTERS),
            dbc.Stack(
                [
                    dbc.Button("Update Filters", id=UPDATE_FILTERS_BTN, color="success", style={"margin": "10px"}),
                    dbc.Button("Draw Frames", id=SHOW_N_FRAMES_BTN, color="primary", style={"margin": "10px"}),
                    dbc.Button("Save Jump File", id=OUT_TO_JUMP_BTN, color="primary", style={"margin": "10px"}),
                ],
                direction="horizontal",
                gap=1,
            ),
        ]
    )
)


@callback(Output(FILTERS, "children"), Input(MAIN_TABLES, "data"), Input(MD_TABLES, "data"))
def init_layout(main_tables, md_tables):
    if not main_tables:
        return no_update

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    columns_options = get_columns_dict(main_tables, md_tables)
    return [get_group_layout(1, columns_options)]


@callback(
    Output({"type": FILTER_LIST, "index": MATCH}, "children"),
    Input({"type": ADD_FILTER_BTN, "index": MATCH}, "n_clicks"),
    Input({"type": ADD_SUB_GROUP, "index": MATCH}, "n_clicks"),
    State({"type": FILTER_LIST, "index": MATCH}, "children"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
)
def add_filters(add_clicks, add_group, filters_list, main_tables, md_tables):
    if not any([add_clicks, add_group]) or not callback_context.triggered_id:
        return no_update

    patched_children = Patch()
    empty_index = None
    for ind in range(len(filters_list) - 1, -1, -1):
        single_filter = filters_list[ind]
        if single_filter["props"]["style"].get("display") == "none":
            empty_index = single_filter["props"]["id"]["index"]
            del patched_children[ind]

    if (not empty_index) and len(filters_list) < MAX_FILTERS_PER_GROUP:
        group_ind = callback_context.triggered_id["index"]
        base_ind = group_ind * MAX_FILTERS_PER_GROUP
        empty_index = get_empty_index(base_ind, filters_list)

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    button_type = callback_context.triggered_id["type"]
    columns_options = get_columns_dict(main_tables, md_tables)
    if button_type == ADD_FILTER_BTN and empty_index:
        patched_children.append(get_filter_row_initial_layout(empty_index, columns_options))
    elif button_type == ADD_SUB_GROUP and empty_index:
        patched_children.append(get_group_layout(empty_index, columns_options))

    return patched_children


def get_empty_index(base_ind, filters_list):
    existing_indexes = set(single_filter["props"]["id"]["index"] for single_filter in filters_list)
    for ind in range(base_ind, base_ind + MAX_FILTERS_PER_GROUP):
        if ind not in existing_indexes:
            return ind
    return None


@callback(
    Output({"type": FILTER_ROW, "index": MATCH}, "style"),
    Input({"type": "remove_filter_btn", "index": MATCH}, "n_clicks"),
)
def remove_filter(remove_clicks):
    if not remove_clicks or not callback_context.triggered_id:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "none"
    return patched_style


@callback(
    Output({"type": FILTER_GROUP, "index": MATCH}, "style"),
    Input({"type": REMOVE_SUB_GROUP, "index": MATCH}, "n_clicks"),
)
def remove_sub_group(remove_clicks):
    if not remove_clicks or not callback_context.triggered_id:
        return no_update

    if callback_context.triggered_id["index"] == 1:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "none"
    return patched_style


@callback(
    Output({"type": MD_OPERATION, "index": MATCH}, "options"),
    Output({"type": MD_OPERATION, "index": MATCH}, "value"),
    Input({"type": MD_COLUMNS, "index": MATCH}, "value"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
)
def update_operation_dropdown_options(column, main_tables, md_tables):
    if not column or not main_tables:
        return {}, ""

    if not callback_context.triggered_id:
        return no_update, no_update

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    column = get_existing_column(column, main_tables, md_tables)
    return column.options, ""


@callback(
    Output({"type": MD_VAL_COL, "index": MATCH}, "children"),
    Input({"type": MD_OPERATION, "index": MATCH}, "value"),
    State({"type": MD_OPERATION, "index": MATCH}, "id"),
    State({"type": MD_COLUMNS, "index": MATCH}, "value"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
)
def update_meta_data_values_options(operation, index, column, main_tables, md_tables):
    curr_index = index["index"]
    if not column or not operation:
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "block"},
            placeholder="----",
            value="",
            type="text",
        )

    if not callback_context.triggered_id:
        return no_update

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    column = get_existing_column(column, main_tables, md_tables)
    if operation in ["IS NULL", "IS NOT NULL"]:
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "none"},
            placeholder="----",
            value="",
            type="text",
        )
    elif operation in ["=", "<>", "IN", "NOT IN"] and isinstance(column, (StringColumn, BoolColumn)):
        multi = operation in ["IN", "NOT IN"]
        distinguish_values = (
            {f"'{val}'": val for val in column.distinct_values}
            if isinstance(column, StringColumn)
            else {val.title(): val for val in column.distinct_values}
        )
        return dcc.Dropdown(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "block"},
            multi=multi,
            clearable=True,
            placeholder="----",
            value="",
            options=distinguish_values,
        )
    else:
        input_type = "text" if isinstance(column, (StringColumn, BoolColumn)) else "number"
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
            placeholder="----",
            value="",
            type=input_type,
        )
