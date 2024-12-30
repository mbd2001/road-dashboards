import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, callback, dcc, html, no_update
from pypika import Criterion, EmptyCriterion, Query, functions
from pypika.queries import QueryBuilder
from pypika.terms import Term

from road_dashboards.road_dump_dashboard.graphical_components.confusion_matrix import get_confusion_matrix
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import join_on_obj_id
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    execute,
    get_main_and_secondary_columns,
    load_object,
    optional_inputs,
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
        main_table: str,
        page_filters_id: str = "",
        title: str = "",
        column: Term | None = None,
        columns_dropdown_id: str = "",
        filter: Criterion = EmptyCriterion(),
        full_grid_row: bool = False,
        component_id: str = "",
    ):
        self.main_dataset_dropdown_id = main_dataset_dropdown_id
        self.secondary_dataset_dropdown_id = secondary_dataset_dropdown_id
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.title = title
        self.column = column
        self.columns_dropdown_id = columns_dropdown_id
        self.filter = filter
        assert (
            self.column or self.columns_dropdown_id
        ), "you have to provide input column, explicitly or through dropdown"
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
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.secondary_dataset_dropdown_id, "value"),
            Input(self.filter_ignores_btn_id, "on"),
            Input(self.main_table, "data"),
            State(META_DATA, "data"),
            optional_inputs(
                page_filters=Input(self.page_filters_id, "data"),
                column=Input(self.columns_dropdown_id, "value"),
            ),
        )
        def get_conf_mat(main_dump, secondary_dump, filter_ignores, main_tables, md_tables, optional):
            if not main_tables or not main_dump or not secondary_dump:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            column: Term = self.column or getattr(type(main_tables[0]), optional["column"], None)
            if not column:
                return no_update

            md_tables: list[Base] = load_object(md_tables)
            page_filters: str = optional.get("page_filters", None)
            page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()

            conf_query = self.conf_mat_subquery(
                main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                main_md=[table for table in md_tables if table.dataset_name == main_dump],
                secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                group_by_column=column,
                data_filter=self.filter if filter_ignores else EmptyCriterion(),
                page_filters=page_filters,
            )
            data = execute(conf_query)
            main_val, secondary_val = get_main_and_secondary_columns(column)
            title = self.title or f"{column.alias.title()} Classification"
            fig = get_confusion_matrix(
                data, main_val.alias, secondary_val.alias, x_label=secondary_dump, y_label=main_dump, title=title
            )
            return fig

    @staticmethod
    def conf_mat_subquery(
        main_labels: list[Base],
        secondary_labels: list[Base],
        main_md: list[Base],
        secondary_md: list[Base],
        group_by_column: Term,
        data_filter: Criterion = EmptyCriterion(),
        page_filters: Criterion = EmptyCriterion(),
    ) -> QueryBuilder:
        join_query, _, _ = join_on_obj_id(
            main_tables=main_labels,
            main_md=main_md,
            secondary_tables=secondary_labels,
            secondary_md=secondary_md,
            diff_terms=[group_by_column],
            data_filter=data_filter,
            page_filters=page_filters,
        )
        first_group_by_column, second_group_by_column = get_main_and_secondary_columns(group_by_column)
        group_by_query = (
            Query.from_(join_query)
            .groupby(first_group_by_column, second_group_by_column)
            .select(first_group_by_column, second_group_by_column, functions.Count("*", "overall"))
        )
        return group_by_query
