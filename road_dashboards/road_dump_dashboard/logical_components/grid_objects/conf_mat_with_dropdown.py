import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update
from pypika import Criterion

from road_dashboards.road_dump_dashboard.graphical_components.confusion_matrix import get_confusion_matrix
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    conf_mat_subquery,
    diff_ids_subquery,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import df_to_jump, execute, load_object


class ConfMatGraphWithDropdown(GridObject):
    """
    Defines the properties of group by graph
    """

    FRAMES_LIMIT = 2048

    def __init__(
        self,
        main_dataset_dropdown_id: str,
        secondary_dataset_dropdown_id: str,
        page_filters_id: str,
        main_table: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_dataset_dropdown_id: str = main_dataset_dropdown_id
        self.secondary_dataset_dropdown_id: str = secondary_dataset_dropdown_id
        self.page_filters_id: str = page_filters_id
        self.main_table = main_table
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.conf_mat_id = self._generate_id("conf_mat")
        self.columns_dropdown_id = self._generate_id("columns_dropdown")
        self.show_diff_btn_id = self._generate_id("show_diff_btn")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")
        self.download_jump_id = self._generate_id("download_jump")

    def layout(self):
        mat_row = dbc.Row(
            loading_wrapper(
                dcc.Graph(
                    id=self.conf_mat_id,
                    config={"displayModeBar": False},
                )
            )
        )
        draw_diff_button = dbc.Button(
            "Draw Diff Frames",
            id=self.show_diff_btn_id,
        )
        generate_jump_btn = dbc.Button("Save Diff to Jump File", id=self.generate_jump_btn_id, color="primary")
        download_jump = dcc.Download(id=self.download_jump_id)
        buttons_row = dbc.Stack(
            [
                draw_diff_button,
                generate_jump_btn,
            ],
            direction="horizontal",
            gap=2,
        )

        single_mat_layout = html.Div([mat_row, buttons_row, download_jump])
        dynamic_conf_mat = card_wrapper(
            [
                dbc.Row(
                    dcc.Dropdown(
                        id=self.columns_dropdown_id,
                        multi=False,
                        placeholder="Attribute",
                        options=EXISTING_TABLES[self.main_table].get_columns(),
                        value=None,
                    )
                ),
                dbc.Row(single_mat_layout),
            ]
        )
        return dynamic_conf_mat

    def _callbacks(self):
        @callback(
            Output(self.conf_mat_id, "figure"),
            Input(self.columns_dropdown_id, "value"),
            Input(self.page_filters_id, "data"),
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.secondary_dataset_dropdown_id, "value"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
        )
        def get_dynamic_conf_mat(column, page_filters, main_dump, secondary_dump, main_tables, md_tables):
            if not column or not main_tables or not main_dump or not secondary_dump:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)
            column: Column = getattr(EXISTING_TABLES[self.main_table], column, None)

            conf_query = conf_mat_subquery(
                group_by_column=column,
                main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                main_md=[table for table in md_tables if table.dataset_name == main_dump],
                secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                page_filters=page_filters,
            )
            data = execute(conf_query)
            fig = get_confusion_matrix(
                data, x_label=secondary_dump, y_label=main_dump, title=f"{column.alias.title()} Classification"
            )
            return fig

        @callback(
            Output(self.download_jump_id, "data"),
            Input(self.generate_jump_btn_id, "n_clicks"),
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.secondary_dataset_dropdown_id, "value"),
            State(self.main_table, "data"),
            State(META_DATA, "data"),
            State(self.page_filters_id, "data"),
            Input(self.columns_dropdown_id, "value"),
        )
        def generate_jump_file(n_clicks, main_dump, secondary_dump, main_tables, md_tables, page_filters, column):
            if not n_clicks or not main_tables:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)
            column: Column = getattr(EXISTING_TABLES[self.main_table], column, None)

            query = diff_ids_subquery(
                diff_column=column,
                main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                main_md=[table for table in md_tables if table.dataset_name == main_dump],
                secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                page_filters=page_filters,
                limit=self.FRAMES_LIMIT,
            )
            jump_frames = execute(query)
            if jump_frames.empty:
                return no_update

            return dict(content=df_to_jump(jump_frames), filename=f"{column.alias}_diff.jump")
