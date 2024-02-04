import dash_daq as daq
import dash_bootstrap_components as dbc
from dash import html, dcc, MATCH, no_update, State, Input, Output, callback_context, callback, Patch

from road_eval_dashboard.components.components_ids import (
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    MD_COLUMNS_OPTION, URL,
)
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.utils.url_state_utils import hash_to_dict, META_DATA_STATE_KEY, add_state, get_state

NUM_FILTERS_PER_GROUP = 10


def get_filter_row_initial_layout(index, md_columns_options):
    single_filter_initial_layout = dbc.Row(
        id={"type": "filter_row", "index": index},
        children=[
            dbc.Col(
                children=dcc.Dropdown(
                    id={"type": "meta_data_columns", "index": index},
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
                    id={"type": "meta_data_operation", "index": index},
                    style={"minWidth": "100%"},
                    multi=False,
                    clearable=True,
                    placeholder="----",
                    value="",
                ),
            ),
            dbc.Col(
                id={"type": "meta_data_val_col", "index": index},
                children=dcc.Input(
                    id={"type": "meta_data_val", "index": index},
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
        id={"type": "filter_group", "index": index},
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
                        id={"type": "add_filter_btn", "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                    dbc.Button(
                        className=f"fas fa-link",
                        id={"type": "add_sub_group", "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                    dbc.Button(
                        className=f"fas fa-trash",
                        id={"type": "remove_sub_group", "index": index},
                        color="secondary",
                        style={"margin": "10px"},
                    ),
                ],
                direction="horizontal",
                gap=1,
            ),
            html.Div(
                id={"type": "filters_list", "index": index},
                children=[get_filter_row_initial_layout(index * NUM_FILTERS_PER_GROUP, md_columns_options)],
            ),
        ],
        style={"border": "2px lightskyblue solid", "border-radius": "20px", "margin": "20px"},
    )
    return group_layout


layout = html.Div(
    card_wrapper(
        [
            html.Div(id="filters"),
            dbc.Stack(
                dbc.Button("Update Filters", id="update_filters_btn", color="success", style={"margin": "10px"}),
                direction="horizontal",
                gap=1,
            ),
        ]
    )
)


@callback(
    Output("filters", "children"),
    Input(MD_COLUMNS_OPTION, "data"),
    State(URL, "hash"),
    State("filters", "children"),
)
def init_layout(md_columns_options, state, filters):
    meta_data_filters_state = get_state(state, META_DATA_STATE_KEY)
    if not meta_data_filters_state:
        return [get_group_layout(1, md_columns_options)]
    if meta_data_filters_state == filters:
        return no_update
    return meta_data_filters_state

@callback(
    Output({"type": "filters_list", "index": MATCH}, "children"),
    Input({"type": "add_filter_btn", "index": MATCH}, "n_clicks"),
    Input({"type": "add_sub_group", "index": MATCH}, "n_clicks"),
    State({"type": "filters_list", "index": MATCH}, "children"),
    State(MD_COLUMNS_OPTION, "data"),
)
def add_filters(add_clicks, add_group, filters_list, md_columns_options):
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
    if button_type == "add_filter_btn" and empty_index:
        patched_children.append(get_filter_row_initial_layout(empty_index, md_columns_options))
    elif button_type == "add_sub_group" and empty_index:
        patched_children.append(get_group_layout(empty_index, md_columns_options))

    return patched_children


def get_empty_index(base_ind, filters_list):
    existing_indexes = set(single_filter["props"]["id"]["index"] for single_filter in filters_list)
    for ind in range(base_ind, base_ind + NUM_FILTERS_PER_GROUP):
        if ind not in existing_indexes:
            return ind
    return None


@callback(
    Output({"type": "filter_row", "index": MATCH}, "style"),
    Input({"type": "remove_filter_btn", "index": MATCH}, "n_clicks"),
)
def remove_filter(remove_clicks):
    if not remove_clicks or not callback_context.triggered_id:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "none"
    return patched_style


@callback(
    Output({"type": "filter_group", "index": MATCH}, "style"),
    Input({"type": "remove_sub_group", "index": MATCH}, "n_clicks"),
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
    Output({"type": "meta_data_operation", "index": MATCH}, "options"),
    Output({"type": "meta_data_operation", "index": MATCH}, "value"),
    Input({"type": "meta_data_columns", "index": MATCH}, "value"),
    State(MD_COLUMNS_TO_TYPE, "data"),
)
def update_operation_dropdown_options(meta_data_col, meta_data_dict):
    if not meta_data_col or not meta_data_dict:
        return [], ""

    if not callback_context.triggered_id:
        return no_update, no_update

    column_type = meta_data_dict[meta_data_col]
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
    Output({"type": "meta_data_val_col", "index": MATCH}, "children"),
    Input({"type": "meta_data_operation", "index": MATCH}, "value"),
    State({"type": "meta_data_operation", "index": MATCH}, "id"),
    State({"type": "meta_data_columns", "index": MATCH}, "value"),
    State(MD_COLUMNS_TO_DISTINCT_VALUES, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
)
def update_meta_data_values_options(operation, index, col, distinct_values_dict, meta_data_dict):
    # TODO: refactor
    curr_index = index["index"]
    if not col or not operation:
        return dcc.Input(
            id={"type": "meta_data_val", "index": curr_index},
            style={"minWidth": "100%", "display": "block"},
            placeholder="----",
            value="",
            type="text",
        )

    if not callback_context.triggered_id:
        return no_update

    distinguish_values = distinct_values_dict.get(col)
    column_type = meta_data_dict[col]
    if operation in ["IS NULL", "IS NOT NULL"]:
        return dcc.Input(
            id={"type": "meta_data_val", "index": curr_index},
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
                id={"type": "meta_data_val", "index": curr_index},
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
            id={"type": "meta_data_val", "index": curr_index},
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
            id={"type": "meta_data_val", "index": curr_index},
            style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
            placeholder="----",
            value="",
            type=type,
        )


@callback(
    Output(MD_FILTERS, "data", allow_duplicate=True),
    Output(URL, "hash", allow_duplicate=True),
    Input("update_filters_btn", "n_clicks"),
    State(URL, "hash"),
    State("filters", "children"),
    prevent_initial_call=True,
)
def generate_meta_data_filters_string(n_clicks, url_state, filters):
    if not filters:
        return "", no_update

    new_state = add_state(META_DATA_STATE_KEY, filters, url_state)
    first_group = filters[0]
    filters_str = recursive_build_meta_data_filters(first_group)
    return filters_str, new_state


def recursive_build_meta_data_filters(filters):
    # removed filter case
    if filters["props"]["style"].get("display") == "none":
        return ""

    # single filter case
    if filters["props"]["id"]["type"] == "filter_row":
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
    filter_components = [column, operation, parsed_val]
    single_filter = " ".join(component for component in filter_components if component)
    return single_filter