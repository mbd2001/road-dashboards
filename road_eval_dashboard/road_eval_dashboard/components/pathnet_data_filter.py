import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, callback, callback_context, dcc, html, no_update

from road_eval_dashboard.road_eval_dashboard.components.components_ids import PATHNET_FILTERS
from road_eval_dashboard.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.road_eval_dashboard.components.meta_data_filter import parse_one_filter


def get_filter_row_initial_layout(index, md_columns_options):
    single_filter_initial_layout = dbc.Row(
        id={"type": "attr_row", "index": index},
        children=[
            dbc.Col(
                id={"type": "pathnet_data_types_col", "index": index},
                children=dcc.Dropdown(
                    id={"type": "pathnet_data_types", "index": index},
                    style={"minWidth": "100%", "marginBottom": "10px"},
                    multi=False,
                    clearable=True,
                    placeholder="Pathnet-Attribute",
                    value="",
                    options=['"split_role"', '"merge_role"', '"primary_role"'],
                ),
            ),
            dbc.Col(
                id={"type": "pathnet_data_operation_col", "index": index},
                children=dcc.Dropdown(
                    id={"type": "pathnet_data_operation", "index": index},
                    style={"minWidth": "100%", "marginBottom": "10px"},
                    multi=False,
                    clearable=True,
                    placeholder="----",
                    value="",
                ),
            ),
            dbc.Col(
                id={"type": "pathnet_data_val_col", "index": index},
                children=dcc.Input(
                    id={"type": "pathnet_data_val", "index": index},
                    style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
                    placeholder="----",
                    value="",
                    type="text",
                ),
            ),
            dbc.Col(
                dbc.Button("Remove Filter", id={"type": "pathnet_remove_filter_btn", "index": index}, color="secondary")
            ),
        ],
    )
    return single_filter_initial_layout


layout = html.Div(
    card_wrapper(
        [
            html.Div(id="Pathnet-filters", children=[get_filter_row_initial_layout(0, [])]),
            dbc.Row(
                [
                    dbc.Col(dbc.Button("Update Filters", id="pathnet_update_filters_btn", color="success")),
                    dbc.Col(dbc.Button("Add Filter", id="pathnet_add_filter_btn", color="secondary")),
                ]
            ),
        ]
    )
)


@callback(
    Output({"type": "pathnet_data_operation", "index": MATCH}, "options"),
    Output({"type": "pathnet_data_operation", "index": MATCH}, "value"),
    Input({"type": "pathnet_data_types", "index": MATCH}, "value"),
)
def update_operation_dropdown_options(meta_data_col):
    if not meta_data_col:
        return [], ""
    if not callback_context.triggered_id:
        return no_update, no_update
    if meta_data_col:
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
    else:
        options = []
    return options, ""


@callback(
    Output({"type": "pathnet_data_val_col", "index": MATCH}, "children"),
    Input({"type": "pathnet_data_operation", "index": MATCH}, "value"),
    State({"type": "pathnet_data_operation", "index": MATCH}, "id"),
)
def update_pathnet_data_values_options(operation, index):
    curr_index = index["index"]
    if not operation:
        return dcc.Input(
            id={"type": "pathnet_data_val", "index": curr_index},
            style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
            placeholder="----",
            value="",
            type="text",
        )

    if not callback_context.triggered_id:
        return no_update

    distinguish_values = [0, 1, 2, 3]
    return dcc.Dropdown(
        id={"type": "pathnet_data_val", "index": curr_index},
        style={"minWidth": "100%", "marginBottom": "10px", "display": "block"},
        multi=False,
        clearable=True,
        placeholder="----",
        value="",
        options=distinguish_values,
    )
