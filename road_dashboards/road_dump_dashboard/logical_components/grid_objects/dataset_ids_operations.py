import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, no_update
from pypika import Criterion

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import ids_query
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import execute, load_object


class DatasetIDsOperations(GridObject):
    """
    Defines the properties of countries heatmap.
    """

    FRAMES_LIMIT = 2048

    def __init__(
        self,
        main_table: str,
        page_filters_id: str,
        datasets_dropdown_id: str,
        full_grid_row: bool = True,
        component_id: str = "",
    ):
        self.main_table = main_table
        self.page_filters_id = page_filters_id
        self.datasets_dropdown_id = datasets_dropdown_id
        super().__init__(full_grid_row=full_grid_row, component_id=component_id)

    def _generate_ids(self):
        self.show_n_frames_btn_id = self._generate_id("show_n_frames_btn")
        self.generate_jump_btn_id = self._generate_id("generate_jump_btn")
        self.download_jump_id = self._generate_id("download_jump")

    def layout(self):
        buttons_layout = dbc.Stack(
            [
                dbc.Button("Draw Frames", id=self.show_n_frames_btn_id, color="primary", style={"margin": "10px"}),
                dbc.Button("Save Jump File", id=self.generate_jump_btn_id, color="primary", style={"margin": "10px"}),
                dcc.Download(id=self.download_jump_id),
            ],
            direction="horizontal",
            gap=1,
        )
        return buttons_layout

    def _callbacks(self):
        @callback(
            Output(self.download_jump_id, "data"),
            Input(self.generate_jump_btn_id, "n_clicks"),
            State(self.datasets_dropdown_id, "value"),
            State(self.main_table, "data"),
            State(META_DATA, "data"),
            State(self.page_filters_id, "data"),
        )
        def generate_jump_file(n_clicks, chosen_dump, main_tables, md_tables, page_filters):
            if not n_clicks or not main_tables:
                return no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            page_filters: Criterion = load_object(page_filters)

            query = ids_query(
                main_tables=[table for table in main_tables if table.dataset_name == chosen_dump],
                main_md=[table for table in md_tables if table.dataset_name == chosen_dump],
                page_filters=page_filters,
                limit=self.FRAMES_LIMIT,
            )
            jump_frames = execute(query)
            jump_string = (
                jump_frames.to_string(header=False, index=False) + f"\n#format: {' '.join(jump_frames.columns)}"
            )
            return dict(content=jump_string, filename=f"{chosen_dump}.jump")
