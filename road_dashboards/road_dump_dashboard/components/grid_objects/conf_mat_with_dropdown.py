from dataclasses import dataclass

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    DYNAMIC_CONF_MAT,
    DYNAMIC_CONF_MAT_DROPDOWN,
    DYNAMIC_SHOW_DIFF_BTN,
    MAIN_NET_DROPDOWN,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
    SECONDARY_NET_DROPDOWN,
)
from road_dashboards.road_dump_dashboard.components.constants.queries_properties import BaseDataQuery, ConfMatQuery
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import (
    TableType,
    get_columns_dict,
    get_existing_column,
    load_object,
)
from road_dashboards.road_dump_dashboard.graphs.confusion_matrix import get_confusion_matrix


@dataclass
class ConfMatGraphWithDropdown(GridObject):
    """
    Defines the properties of group by graph

    Attributes:
            include_ignore_btn (bool):
    """

    title: str = DYNAMIC_CONF_MAT
    full_grid_row: bool = True

    def layout(self):
        mat_row = dbc.Row(
            loading_wrapper(
                dcc.Graph(
                    id=self.title,
                    config={"displayModeBar": False},
                )
            )
        )
        draw_diff_button = dbc.Button(
            "Draw Diff Frames",
            id=DYNAMIC_SHOW_DIFF_BTN,
            className="bg-primary mt-5",
        )
        buttons_row = dbc.Row(draw_diff_button)
        single_mat_layout = html.Div([mat_row, buttons_row])
        dynamic_conf_mat = html.Div(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=DYNAMIC_CONF_MAT_DROPDOWN,
                        style={"minWidth": "100%"},
                        multi=False,
                        placeholder="Attribute",
                        value="",
                    )
                ),
                dbc.Row(single_mat_layout),
            ]
        )
        return dynamic_conf_mat


@callback(Output(DYNAMIC_CONF_MAT_DROPDOWN, "options"), Input(MAIN_TABLES, "data"))
def init_dynamic_chart_dropdown(main_tables):
    if not main_tables:
        return no_update

    main_tables: TableType = load_object(main_tables)
    columns_options = get_columns_dict(main_tables)
    return columns_options


@callback(
    Output(DYNAMIC_CONF_MAT, "figure"),
    Input(DYNAMIC_CONF_MAT_DROPDOWN, "value"),
    Input(PAGE_FILTERS, "data"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    Input(MAIN_TABLES, "data"),
    Input(MD_TABLES, "data"),
)
def get_dynamic_conf_mat(column, page_filters, main_dump, secondary_dump, main_tables, md_tables):
    if not column or not main_tables or not main_dump or not secondary_dump:
        return no_update

    main_tables: TableType = load_object(main_tables)
    md_tables: TableType = load_object(md_tables) if md_tables else None
    column = get_existing_column(column, main_tables, md_tables)
    query = ConfMatQuery(
        column_to_compare=column,
        main_data_query=BaseDataQuery(
            main_tables=main_tables.tables,
            meta_data_tables=md_tables.tables if md_tables else None,
            page_filters=page_filters,
            dumps_to_include=[main_dump],
            extra_columns=[column],
        ),
        secondary_data_query=BaseDataQuery(
            main_tables=main_tables.tables,
            meta_data_tables=md_tables.tables if md_tables else None,
            page_filters=page_filters,
            dumps_to_include=[secondary_dump],
            extra_columns=[column],
        ),
    )
    data = query.get_results()
    fig = get_confusion_matrix(
        data, x_label=secondary_dump, y_label=main_dump, title=f"{column.name.title()} Classification"
    )
    return fig
