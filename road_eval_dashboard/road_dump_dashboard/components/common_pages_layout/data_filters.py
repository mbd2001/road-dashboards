import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import MATCH, Input, Output, Patch, State, callback, callback_context, dcc, html, no_update

from road_eval_dashboard.road_dump_dashboard.components.constants.components_ids import (
    ADD_FILTER_BTN,
    ADD_SUB_GROUP,
    FILTER_GROUP,
    FILTER_LIST,
    FILTER_ROW,
    FILTERS,
    FILTERS_MAIN_TABLE,
    FILTERS_MD_TABLE,
    MD_COLUMNS,
    MD_FILTERS,
    MD_OPERATION,
    MD_VAL,
    MD_VAL_COL,
    REMOVE_SUB_GROUP,
    TABLES,
    UPDATE_FILTERS_BTN,
)
from road_eval_dashboard.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_eval_dashboard.road_dump_dashboard.components.logical_components.queries_manager import (
    manipulate_column_to_avoid_ambiguities,
)
from road_eval_dashboard.road_dump_dashboard.components.logical_components.tables_properties import (
    get_tables_property_union,
    get_value_from_tables_property_union,
)

NUM_FILTERS_PER_GROUP = 10


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
                children=[get_filter_row_initial_layout(index * NUM_FILTERS_PER_GROUP, md_columns_options)],
            ),
        ],
        style={"border": "2px lightskyblue solid", "border-radius": "20px", "margin": "20px"},
    )
    return group_layout


def layout(main_table, meta_data_table=None):
    empty_layout = html.Div(
        card_wrapper(
            [
                html.Div(id=FILTERS_MAIN_TABLE, children=main_table, style={"display": "none"}),
                html.Div(id=FILTERS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
                html.H3("Filters"),
                html.Div(id=FILTERS),
                dbc.Stack(
                    dbc.Button("Update Filters", id=UPDATE_FILTERS_BTN, color="success", style={"margin": "10px"}),
                    direction="horizontal",
                    gap=1,
                ),
            ]
        )
    )
    return empty_layout


@callback(
    Output(FILTERS, "children"),
    Input(TABLES, "data"),
    State(FILTERS_MAIN_TABLE, "children"),
    State(FILTERS_MD_TABLE, "children"),
)
def init_layout(tables, main_table, meta_data_table):
    if not tables:
        return no_update

    columns_options = get_tables_property_union(tables[main_table], tables.get(meta_data_table))
    return [get_group_layout(1, columns_options)]


@callback(
    Output({"type": FILTER_LIST, "index": MATCH}, "children"),
    Input({"type": ADD_FILTER_BTN, "index": MATCH}, "n_clicks"),
    Input({"type": ADD_SUB_GROUP, "index": MATCH}, "n_clicks"),
    State({"type": FILTER_LIST, "index": MATCH}, "children"),
    State(TABLES, "data"),
    State(FILTERS_MAIN_TABLE, "children"),
    State(FILTERS_MD_TABLE, "children"),
)
def add_filters(add_clicks, add_group, filters_list, tables, main_table, meta_data_table):
    if not any([add_clicks, add_group]) or not callback_context.triggered_id:
        return no_update

    patched_children = Patch()
    empty_index = None
    for ind in range(len(filters_list) - 1, -1, -1):
        single_filter = filters_list[ind]
        if single_filter["props"]["style"].get("display") == "none":
            empty_index = single_filter["props"]["id"]["index"]
            del patched_children[ind]

    if not empty_index and len(filters_list) < NUM_FILTERS_PER_GROUP:
        group_ind = callback_context.triggered_id["index"]
        base_ind = group_ind * NUM_FILTERS_PER_GROUP
        empty_index = get_empty_index(base_ind, filters_list)

    button_type = callback_context.triggered_id["type"]
    columns_options = get_tables_property_union(tables[main_table], tables.get(meta_data_table))
    if button_type == ADD_FILTER_BTN and empty_index:
        patched_children.append(get_filter_row_initial_layout(empty_index, columns_options))
    elif button_type == ADD_SUB_GROUP and empty_index:
        patched_children.append(get_group_layout(empty_index, columns_options))

    return patched_children


def get_empty_index(base_ind, filters_list):
    existing_indexes = set(single_filter["props"]["id"]["index"] for single_filter in filters_list)
    for ind in range(base_ind, base_ind + NUM_FILTERS_PER_GROUP):
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
    State(TABLES, "data"),
    State(FILTERS_MAIN_TABLE, "children"),
    State(FILTERS_MD_TABLE, "children"),
)
def update_operation_dropdown_options(meta_data_col, tables, data_table, meta_data_table):
    if not meta_data_col or not tables:
        return [], ""

    if not callback_context.triggered_id:
        return no_update, no_update

    column_type = get_value_from_tables_property_union(meta_data_col, tables[data_table], tables.get(meta_data_table))
    if column_type.startswith(("int", "float", "double")):
        options = [
            {"label": "Greater", "value": ">"},
            {"label": "Greater or equal", "value": ">="},
            {"label": "Less", "value": "<"},
            {"label": "Less or equal", "value": "<="},
            {"label": "Equal", "value": "="},
            {"label": "Not Equal", "value": "<>"},
            {"label": "Is NULL", "value": "IS NULL"},
            {"label": "Is not NULL", "value": "IS NOT NULL"},
        ]
    elif column_type == "bool":
        options = [
            {"label": "Equal", "value": "="},
            {"label": "Not Equal", "value": "<>"},
            {"label": "Is NULL", "value": "IS NULL"},
            {"label": "Is not NULL", "value": "IS NOT NULL"},
        ]
    elif column_type == "object":
        options = [
            {"label": "Equal", "value": "="},
            {"label": "Not Equal", "value": "<>"},
            {"label": "Like", "value": "LIKE"},
            {"label": "Is NULL", "value": "IS NULL"},
            {"label": "Is not NULL", "value": "IS NOT NULL"},
            {"label": "In", "value": "IN"},
            {"label": "Not In", "value": "NOT IN"},
        ]
    else:
        options = []

    return options, ""


@callback(
    Output({"type": MD_VAL_COL, "index": MATCH}, "children"),
    Input({"type": MD_OPERATION, "index": MATCH}, "value"),
    State({"type": MD_OPERATION, "index": MATCH}, "id"),
    State({"type": MD_COLUMNS, "index": MATCH}, "value"),
    State(TABLES, "data"),
    State(FILTERS_MAIN_TABLE, "children"),
    State(FILTERS_MD_TABLE, "children"),
)
def update_meta_data_values_options(operation, index, col, tables, main_table, meta_data_table):
    # TODO: refactor
    curr_index = index["index"]
    if not col or not operation:
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "block"},
            placeholder="----",
            value="",
            type="text",
        )

    if not callback_context.triggered_id:
        return no_update

    distinguish_values = get_value_from_tables_property_union(
        col, tables[main_table], tables.get(meta_data_table), "columns_distinguish_values"
    )
    column_type = get_value_from_tables_property_union(col, tables[main_table], tables.get(meta_data_table))
    if operation in ["IS NULL", "IS NOT NULL"]:
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "none"},
            placeholder="----",
            value="",
            type="text",
        )
    elif operation in ["IN", "NOT IN"]:
        if column_type in ["object", "bool"]:
            distinguish_values = (
                distinguish_values
                if column_type == "object"
                else [{"label": "True", "value": "True"}, {"label": "False", "value": "False"}]
            )
            return dcc.Dropdown(
                id={"type": MD_VAL, "index": curr_index},
                style={"minWidth": "100%", "display": "block"},
                multi=True,
                clearable=True,
                placeholder="----",
                value="",
                options=distinguish_values,
            )
    elif operation in ["=", "<>"] and column_type in ["object", "bool"]:
        distinguish_values = (
            distinguish_values
            if column_type == "object"
            else [{"label": "True", "value": "TRUE"}, {"label": "False", "value": "FALSE"}]
        )
        return dcc.Dropdown(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "display": "block"},
            multi=False,
            clearable=True,
            placeholder="----",
            value="",
            options=distinguish_values,
        )
    else:
        type = "text" if column_type in ["object", "bool"] else "number"
        return dcc.Input(
            id={"type": MD_VAL, "index": curr_index},
            style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
            placeholder="----",
            value="",
            type=type,
        )


@callback(
    Output(MD_FILTERS, "data"),
    Input(UPDATE_FILTERS_BTN, "n_clicks"),
    State(FILTERS, "children"),
)
def generate_meta_data_filters_string(n_clicks, filters):
    if not filters:
        return ""

    first_group = filters[0]
    filters_str = recursive_build_meta_data_filters(first_group)
    return filters_str


def recursive_build_meta_data_filters(filters):
    # removed filter case
    if filters["props"]["style"].get("display") == "none":
        return ""

    # single filter case
    if filters["props"]["id"]["type"] == FILTER_ROW:
        row = filters["props"]
        column = row["children"][0]["props"]["children"]["props"]["value"]
        operation = row["children"][1]["props"]["children"]["props"]["value"]
        value = row["children"][2]["props"]["children"]["props"]["value"]
        single_filter = parse_one_filter(column, operation, value)
        return single_filter

    # group case
    and_or_is_on = filters["props"]["children"][0]["props"]["children"][0]["props"]["on"]
    and_or_operator = " OR " if and_or_is_on else " AND "
    filters = filters["props"]["children"][1]["props"]["children"]
    sub_filters = [recursive_build_meta_data_filters(flt) for flt in filters]
    filters_str = and_or_operator.join(sub_filter for sub_filter in sub_filters if sub_filter)
    return filters_str


def parse_one_filter(column, operation, value):
    if operation == "LIKE":
        parsed_val = f"'{value}'"
    elif operation == "IN":
        parsed_val = f"({', '.join(val for val in value)})"
    else:
        parsed_val = str(value)

    column = manipulate_column_to_avoid_ambiguities(column)
    filter_components = [column, operation, parsed_val]
    single_filter = " ".join(component for component in filter_components if component)
    return single_filter
