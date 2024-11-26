import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, dcc, html, no_update
from pypika import Criterion, EmptyCriterion
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.graphical_components.confusion_matrix import get_confusion_matrix
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import conf_mat_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    execute,
    get_main_and_secondary_columns,
    load_object,
)


class ConfMatGraph(GridObject):
    """
    Defines the properties of confusion matrix graph

    Attributes:
            column (Term): column to compare between two datasets
            filter (str): optional. filter to apply on the datasets
    """

    def __init__(
        self,
        main_dataset_dropdown_id: str,
        secondary_dataset_dropdown_id: str,
        page_filters_id: str,
        main_table: str,
        title: str,
        column: Term,
        filter: Criterion = EmptyCriterion(),
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.title = title
        self.column = column
        self.filter = filter
        self.main_dataset_dropdown_id = main_dataset_dropdown_id
        self.secondary_dataset_dropdown_id = secondary_dataset_dropdown_id
        self.page_filters_id = page_filters_id
        self.main_table = main_table
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.conf_mat_id = self._generate_id("conf_mat")
        self.filter_ignores_btn_id = self._generate_id("filter_ignores_btn")
        self.show_diff_btn_id = self._generate_id("show_diff_btn")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")

    def layout(self):
        mat_row = loading_wrapper(
            dcc.Graph(
                id=self.conf_mat_id,
                config={"displayModeBar": False},
            )
        )
        draw_diff_button = dbc.Button(
            "Draw Diff Frames",
            id=self.show_diff_btn_id,
        )
        filter_ignores_button = daq.BooleanSwitch(
            id=self.filter_ignores_btn_id,
            on=False,
            label="Show All <-> Filter Ignores",
            labelPosition="top",
        )

        generate_jump_btn = dbc.Button("Save Diff to Jump File", id=self.generate_jump_btn_id, color="primary")
        buttons_row = dbc.Stack(
            [
                draw_diff_button,
                generate_jump_btn,
                html.Div(filter_ignores_button, hidden=isinstance(self.filter, EmptyCriterion)),
            ],
            direction="horizontal",
            gap=2,
        )

        single_mat_layout = card_wrapper([mat_row, buttons_row])
        return single_mat_layout

    def _callbacks(self):
        @callback(
            Output(self.conf_mat_id, "figure"),
            Input(self.page_filters_id, "data"),
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.secondary_dataset_dropdown_id, "value"),
            Input(self.filter_ignores_btn_id, "on"),
            Input(self.main_table, "data"),
            State(META_DATA, "data"),
        )
        def get_conf_mat(page_filters, main_dump, secondary_dump, filter_ignores, main_tables, md_tables):
            if not main_tables or not main_dump or not secondary_dump:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)

            conf_query = conf_mat_subquery(
                main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                main_md=[table for table in md_tables if table.dataset_name == main_dump],
                secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                group_by_column=self.column,
                data_filter=self.filter if filter_ignores else EmptyCriterion(),
                page_filters=page_filters,
            )
            data = execute(conf_query)
            main_val, secondary_val = get_main_and_secondary_columns(self.column)
            fig = get_confusion_matrix(
                data, main_val.alias, secondary_val.alias, x_label=secondary_dump, y_label=main_dump, title=self.title
            )
            return fig
