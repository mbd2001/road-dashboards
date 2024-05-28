import dash_bootstrap_components as dbc
from dash import MATCH, Input, Output, Patch, State, callback, dcc, html, no_update
from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.road_dump_dashboard.components.constants.components_ids import (
    CONF_MATS_LABELS_TABLE,
    CONF_MATS_MAIN_TABLE,
    CONF_MATS_MD_TABLE,
    DISPLAY_CONF_MATS,
    DYNAMIC_CONF_DROPDOWN,
    DYNAMIC_CONF_MAT,
    DYNAMIC_SHOW_DIFF_IDX,
    GENERIC_CONF_MAT,
    GENERIC_SHOW_DIFF_BTN,
    MAIN_NET_DROPDOWN,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    SECONDARY_NET_DROPDOWN,
    TABLES,
)
from road_eval_dashboard.road_dump_dashboard.components.dashboard_layout.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_eval_dashboard.road_dump_dashboard.components.graph_wrappers import frames_carousel
from road_eval_dashboard.road_dump_dashboard.components.logical_components.queries_manager import (
    generate_conf_mat_query,
)
from road_eval_dashboard.road_dump_dashboard.components.logical_components.tables_properties import (
    get_tables_property_union,
)
from road_eval_dashboard.road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix


def layout(main_table, columns_to_compare, meta_data_table=None, labels_table=None):
    if labels_table is None:
        labels_table = main_table

    matrices_layout = html.Div(
        id=DISPLAY_CONF_MATS,
        children=[
            html.Div(id=CONF_MATS_MAIN_TABLE, children=main_table, style={"display": "none"}),
            html.Div(id=CONF_MATS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
            html.Div(id=CONF_MATS_LABELS_TABLE, children=labels_table, style={"display": "none"}),
            card_wrapper(
                [
                    nets_selection_layout(),
                    dynamic_conf_mat_layout(),
                    *generic_rows_layout(columns_to_compare),
                ]
            ),
            frames_carousel.layout(),
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


def dynamic_conf_mat_layout():
    dynamic_conf_mat = dbc.Row(
        [
            dcc.Dropdown(
                id=DYNAMIC_CONF_DROPDOWN,
                multi=False,
                placeholder="----",
                value="",
            ),
            get_single_mat_layout(DYNAMIC_CONF_MAT, {"type": GENERIC_SHOW_DIFF_BTN, "index": DYNAMIC_SHOW_DIFF_IDX}),
        ]
    )

    return dynamic_conf_mat


def generic_rows_layout(columns_to_compare):
    list_columns_tuples = [tuple(columns_to_compare[i : i + 2]) for i in range(0, len(columns_to_compare), 2)]
    generic_rows = [
        dbc.Row(
            [
                dbc.Col(
                    get_single_mat_layout(
                        {"type": GENERIC_CONF_MAT, "index": col_to_compare},
                        {"type": GENERIC_SHOW_DIFF_BTN, "index": col_to_compare},
                    )
                )
                for col_to_compare in columns_tuple
            ]
        )
        for columns_tuple in list_columns_tuples
    ]

    return generic_rows


def get_single_mat_layout(mat_id, diff_btn_id):
    mat_layout = html.Div(
        [
            loading_wrapper(
                dcc.Graph(
                    id=mat_id,
                    config={"displayModeBar": False},
                )
            ),
            dbc.Button(
                "Draw Diff Frames",
                id=diff_btn_id,
                className="bg-primary mt-5",
            ),
        ]
    )
    return mat_layout


@callback(
    Output(DISPLAY_CONF_MATS, "style"),
    Input(TABLES, "data"),
)
def init_dumps_dropdown(tables):
    if not tables or len(tables["names"]) <= 1:
        return no_update

    patched_style = Patch()
    patched_style["display"] = "block"
    return patched_style


@callback(
    Output(MAIN_NET_DROPDOWN, "options"),
    Output(MAIN_NET_DROPDOWN, "label"),
    Output(MAIN_NET_DROPDOWN, "value"),
    Output(SECONDARY_NET_DROPDOWN, "options"),
    Output(SECONDARY_NET_DROPDOWN, "label"),
    Output(SECONDARY_NET_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_dumps_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update, no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in tables["names"]]
    if len(options) < 2:
        return options, options[0]["label"], options[0]["value"], no_update, no_update, no_update

    return options, options[0]["label"], options[0]["value"], options, options[1]["label"], options[1]["value"]


@callback(
    Output({"type": GENERIC_CONF_MAT, "index": MATCH}, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    State({"type": GENERIC_CONF_MAT, "index": MATCH}, "id"),
    State(CONF_MATS_MAIN_TABLE, "children"),
    State(CONF_MATS_MD_TABLE, "children"),
)
def get_generic_conf_mat(
    meta_data_filters, tables, population, main_dump, secondary_dump, col_to_compare, main_table, meta_data_table
):
    if not population or not tables or not main_dump or not secondary_dump:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    col_to_compare = col_to_compare["index"]
    fig = get_conf_mat_fig(
        main_tables, col_to_compare, main_dump, secondary_dump, population, meta_data_tables, meta_data_filters
    )
    return fig


@callback(
    Output(DYNAMIC_CONF_DROPDOWN, "options"),
    Input(TABLES, "data"),
    State(CONF_MATS_MAIN_TABLE, "children"),
)
def init_dynamic_conf_dropdown(tables, main_table):
    if not tables:
        return no_update

    columns_options = get_tables_property_union(tables[main_table])
    return columns_options


@callback(
    Output(DYNAMIC_CONF_MAT, "figure"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    Input(DYNAMIC_CONF_DROPDOWN, "value"),
    State(CONF_MATS_MAIN_TABLE, "children"),
    State(CONF_MATS_MD_TABLE, "children"),
)
def get_dynamic_conf_mat(
    meta_data_filters, tables, population, main_dump, secondary_dump, dynamic_col, main_table, meta_data_table
):
    if not population or not tables or not main_dump or not secondary_dump or not dynamic_col:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    col_to_compare = dynamic_col
    fig = get_conf_mat_fig(
        main_tables, col_to_compare, main_dump, secondary_dump, population, meta_data_tables, meta_data_filters
    )
    return fig


def get_conf_mat_fig(
    main_tables, col_to_compare, main_dump, secondary_dump, population, meta_data_tables=None, meta_data_filters=None
):
    query = generate_conf_mat_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        col_to_compare,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
    )

    data, _ = query_athena(database="run_eval_db", query=query)
    fig = get_confusion_matrix(
        data, x_label=secondary_dump, y_label=main_dump, title=f"{col_to_compare.title()} Confusion Matrix"
    )
    return fig
