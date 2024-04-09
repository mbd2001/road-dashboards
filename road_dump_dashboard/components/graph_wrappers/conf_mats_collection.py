import dash_bootstrap_components as dbc
from dash import html, register_page, dcc, callback, Output, Input, State, no_update, MATCH, callback_context
from road_database_toolkit.athena.athena_utils import query_athena

from road_dump_dashboard.components.constants.components_ids import (
    SECONDARY_NET_DROPDOWN,
    MAIN_NET_DROPDOWN,
    GENERIC_CONF_MAT,
    DYNAMIC_CONF_DROPDOWN,
    DYNAMIC_CONF_MAT,
    TABLES,
    MD_FILTERS,
    POPULATION_DROPDOWN,
    GENERIC_SHOW_DIFF_BTN,
    DYNAMIC_SHOW_DIFF_IDX,
    CONF_MATS_MAIN_TABLE,
    CONF_MATS_MD_TABLE,
)
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper, loading_wrapper
from road_dump_dashboard.components.graph_wrappers import frames_display
from road_dump_dashboard.components.logical_components.queries_manager import generate_conf_mat_query
from road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix


def layout(main_table, meta_data_table=None, columns_to_compare=None):
    if columns_to_compare is None:
        columns_to_compare = []

    matrices_layout = html.Div(
        [
            html.Div(id=CONF_MATS_MAIN_TABLE, children=main_table, style={"display": "none"}),
            html.Div(id=CONF_MATS_MD_TABLE, children=meta_data_table, style={"display": "none"}),
            card_wrapper(
                [
                    nets_selection_layout(),
                    dynamic_conf_mat_layout(),
                    *generic_rows_layout(columns_to_compare),
                ]
            ),
            frames_display.layout,
        ]
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
            loading_wrapper([dcc.Graph(id=DYNAMIC_CONF_MAT, config={"displayModeBar": False})]),
            dbc.Button(
                "Draw Diff Frames",
                id={"type": GENERIC_SHOW_DIFF_BTN, "index": DYNAMIC_SHOW_DIFF_IDX},
                className="bg-primary mt-5",
            ),
        ]
    )

    return dynamic_conf_mat


def generic_rows_layout(columns_to_compare):
    if not columns_to_compare:
        return [None]

    list_columns_tuples = [tuple(columns_to_compare[i : i + 2]) for i in range(0, len(columns_to_compare), 2)]
    generic_rows = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        loading_wrapper(
                            dcc.Graph(
                                id={"type": GENERIC_CONF_MAT, "index": col_to_compare},
                                config={"displayModeBar": False},
                            )
                        ),
                        dbc.Button(
                            "Draw Diff Frames",
                            id={"type": GENERIC_SHOW_DIFF_BTN, "index": col_to_compare},
                            className="bg-primary mt-5",
                        ),
                    ]
                )
                for col_to_compare in columns_tuple
            ]
        )
        for columns_tuple in list_columns_tuples
    ]

    return generic_rows


@callback(
    Output(MAIN_NET_DROPDOWN, "options"),
    Output(MAIN_NET_DROPDOWN, "label"),
    Output(MAIN_NET_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_main_dump_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in tables["names"]]
    return options, options[0]["label"], options[0]["value"]


@callback(
    Output(SECONDARY_NET_DROPDOWN, "options"),
    Output(SECONDARY_NET_DROPDOWN, "label"),
    Output(SECONDARY_NET_DROPDOWN, "value"),
    Input(TABLES, "data"),
)
def init_secondary_dump_dropdown(tables):
    if not tables:
        return no_update, no_update, no_update

    options = [{"label": name.title(), "value": name} for name in tables["names"]]
    return options, options[1]["label"], options[1]["value"]


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
    background=True,
)
def get_generic_conf_mat(
    meta_data_filters, tables, population, main_dump, secondary_dump, col_to_compare, main_table, meta_data_table
):
    if not population or not tables or not main_dump or not secondary_dump:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    col_to_compare = col_to_compare["index"]
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


@callback(
    Output(DYNAMIC_CONF_DROPDOWN, "options"),
    Input(TABLES, "data"),
)
def init_dynamic_conf_dropdown(tables):
    if not tables:
        return no_update

    columns_options = tables["meta_data"]["columns_options"]
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
    background=True,
)
def get_dynamic_conf_mat(
    meta_data_filters, tables, population, main_dump, secondary_dump, dynamic_col, main_table, meta_data_table
):
    if not population or not tables or not main_dump or not secondary_dump or not dynamic_col:
        return no_update

    main_tables = tables[main_table]
    meta_data_tables = tables.get(meta_data_table)
    column_to_compare = dynamic_col
    query = generate_conf_mat_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        column_to_compare,
        meta_data_tables=meta_data_tables,
        meta_data_filters=meta_data_filters,
    )

    data, _ = query_athena(database="run_eval_db", query=query)
    fig = get_confusion_matrix(
        data, x_label=secondary_dump, y_label=main_dump, title=f"{dynamic_col.title()} Confusion Matrix"
    )
    return fig
