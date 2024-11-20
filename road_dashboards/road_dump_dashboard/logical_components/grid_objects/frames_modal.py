import dash_bootstrap_components as dbc
import numpy as np
import orjson
import pandas as pd
from dash import (
    Input,
    Output,
    Patch,
    State,
    callback,
    callback_context,
    clientside_callback,
    dcc,
    html,
    no_update,
    set_props,
)
from pypika import EmptyCriterion
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

from road_dashboards.road_dump_dashboard.graphical_components.frame_drawer import draw_img, draw_top_view
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import diff_labels_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_with_dropdown import (
    ConfMatGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object, execute, load_object


class FramesModal(GridObject):
    IMG_LIMIT = 64

    def __init__(
        self,
        page_filters_id: str,
        main_table: str,
        triggering_conf_mats: list[ConfMatGraph] = None,
        triggering_dropdown_conf_mats: list[ConfMatGraphWithDropdown] = None,
        component_id: str = "",
    ):
        self.page_filters_id = page_filters_id
        self.main_table = main_table
        self.triggering_conf_mats = triggering_conf_mats
        self.triggering_dropdown_conf_mats = triggering_dropdown_conf_mats
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        self.curr_img_index_id = self._generate_id("curr_img_index")
        self.curr_num_of_drawn_datasets_id = self._generate_id("curr_num_of_drawn_datasets")
        self.curr_query_id = self._generate_id("curr_query")

        self.images_layout_id = self._generate_id("images_layout")
        self.next_btn_id = self._generate_id("next_btn")
        self.prev_btn_id = self._generate_id("prev_btn")

    def layout(self):
        frames_layout = dbc.Modal(
            [
                dcc.Store(id=self.curr_img_index_id, data=0),
                dcc.Store(id=self.curr_num_of_drawn_datasets_id),
                dcc.Store(id=self.curr_query_id),
                html.Div(id=self.prev_btn_id, hidden=True),
                html.Div(id=self.next_btn_id, hidden=True),
                loading_wrapper(html.Div(dcc.Graph(config={"displayModeBar": False}), id=self.images_layout_id)),
            ],
            id=self.component_id,
            is_open=False,
            className="mw-100 p-5",
        )
        return frames_layout

    def _callbacks(self):
        for conf_mat in self.triggering_conf_mats:

            @callback(
                Output(conf_mat.filter_ignores_btn_id, "on"),
                Input(conf_mat.show_diff_btn_id, "n_clicks"),
                Input(conf_mat.filter_ignores_btn_id, "on"),
                State(self.page_filters_id, "data"),
                State(self.main_table, "data"),
                State(META_DATA, "data"),
                State(conf_mat.main_dataset_dropdown_id, "value"),
                State(conf_mat.secondary_dataset_dropdown_id, "value"),
                prevent_initial_call=True,
            )
            def draw_diffs_generic_case(
                show_diff_n_clicks,
                filter_ignores,
                filters,
                main_tables,
                md_tables,
                main_dump,
                secondary_dump,
            ):
                if not show_diff_n_clicks or not main_tables or not md_tables or not main_dump or not secondary_dump:
                    return no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                extra_columns = list(
                    main_tables[0].get_columns(names_only=False, include_list_columns=True, only_drawable=True)
                )
                query = diff_labels_subquery(
                    diff_column=conf_mat.column,
                    label_columns=extra_columns,
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    data_filter=conf_mat.filter if filter_ignores else EmptyCriterion(),
                    page_filters=load_object(filters),
                    limit=self.IMG_LIMIT,
                )

                set_props(self.curr_query_id, {"data": dump_object(query)})
                set_props(self.component_id, {"is_open": True})
                return filter_ignores

        for dropdown_conf_mat in self.triggering_dropdown_conf_mats:

            @callback(
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                State(self.page_filters_id, "data"),
                State(self.main_table, "data"),
                State(META_DATA, "data"),
                State(dropdown_conf_mat.main_dataset_dropdown_id, "value"),
                State(dropdown_conf_mat.secondary_dataset_dropdown_id, "value"),
                Input(dropdown_conf_mat.columns_dropdown_id, "value"),
                Input(dropdown_conf_mat.show_diff_btn_id, "n_clicks"),
                prevent_initial_call=True,
            )
            def draw_diffs_dynamic_case(
                filters,
                main_tables,
                md_tables,
                main_dump,
                secondary_dump,
                dynamic_column,
                show_diff_n_clicks,
            ):
                if (
                    not show_diff_n_clicks
                    or not main_tables
                    or not md_tables
                    or not main_dump
                    or not secondary_dump
                    or not dynamic_column
                ):
                    return no_update, no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                extra_columns = list(
                    main_tables[0].get_columns(names_only=False, include_list_columns=True, only_drawable=True)
                )
                dynamic_column = load_object(dynamic_column)
                query = diff_labels_subquery(
                    diff_column=dynamic_column,
                    label_columns=extra_columns,
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    page_filters=load_object(filters),
                    limit=self.IMG_LIMIT,
                )

                return query, True

        clientside_callback(
            """
                function(id) {{
                    document.addEventListener("keydown", function(event) {{
                        if (event.key == 'ArrowLeft') {{
                            document.getElementById('{prev_btn_id}').click()
                            event.stopPropagation()
                        }}
                        if (event.key == 'ArrowRight') {{
                            document.getElementById('{next_btn_id}').click()
                            event.stopPropagation()
                        }}
                    }});
                    return window.dash_clientside.no_update
                }}
            """.format(next_btn_id=self.next_btn_id, prev_btn_id=self.prev_btn_id),
            Output(self.component_id, "id"),
            Input(self.component_id, "id"),
        )

        @callback(
            Output(self.images_layout_id, "children"),
            Output(self.curr_num_of_drawn_datasets_id, "data"),
            Output(self.curr_img_index_id, "data"),
            Input(self.curr_query_id, "data"),
            prevent_initial_call=True,
        )
        def init_frame_graphs(
            curr_query,
        ):
            data = execute(load_object(curr_query))
            images_layout = self.generate_layout_from_query_data(data)
            return images_layout, len(images_layout), 0

        @callback(
            Output(self.images_layout_id, "children", allow_duplicate=True),
            Output(self.curr_img_index_id, "data", allow_duplicate=True),
            Input(self.prev_btn_id, "n_clicks"),
            Input(self.next_btn_id, "n_clicks"),
            State(self.curr_img_index_id, "data"),
            State(self.curr_num_of_drawn_datasets_id, "data"),
            prevent_initial_call=True,
        )
        def update_frame_graphs(
            prev_n_clicks,
            next_n_clicks,
            img_ind,
            curr_num_of_drawn_datasets_id,
        ):
            triggered_id = callback_context.triggered_id
            if not triggered_id:
                return no_update, no_update

            images_layout = Patch()
            n_clicks = callback_context.triggered[0]["value"]
            if n_clicks == 0:
                return no_update, no_update, no_update, no_update, no_update

            for i in range(curr_num_of_drawn_datasets_id):
                images_layout[i]["props"]["children"][0]["props"]["children"]["props"]["children"][img_ind]["props"][
                    "style"
                ]["display"] = "none"
                images_layout[i]["props"]["children"][1]["props"]["children"]["props"]["children"][img_ind]["props"][
                    "style"
                ]["display"] = "none"

            if triggered_id == self.prev_btn_id:
                img_ind = (img_ind - 1) % self.IMG_LIMIT
            elif triggered_id == self.next_btn_id:
                img_ind = (img_ind + 1) % self.IMG_LIMIT

            for dataset_ind in range(curr_num_of_drawn_datasets_id):
                images_layout[dataset_ind]["props"]["children"][0]["props"]["children"]["props"]["children"][img_ind][
                    "props"
                ]["style"]["display"] = "block"
                images_layout[dataset_ind]["props"]["children"][1]["props"]["children"]["props"]["children"][img_ind][
                    "props"
                ]["style"]["display"] = "block"

            return images_layout, img_ind

    @staticmethod
    def generate_layout_from_query_data(data: pd.DataFrame):
        labels_df = FramesModal.parse_labels_df(data)

        indexes_df = labels_df[["clip_name", "grabindex"]].drop_duplicates()
        clip_names = indexes_df.clip_name
        grab_indexes = [int(gi) for gi in indexes_df.grabindex]
        data_types = ["data"] * len(clip_names)
        images = DroneViewDBManager.load_multiple_clips_images(clip_names, grab_indexes, data_types)

        dumps_df_list = [d for _, d in labels_df.groupby(["dump_name"])]
        final_layout = []
        for dump_df in dumps_df_list:
            frames_df_list = [i for _, i in dump_df.groupby(["clip_name", "grabindex"])]
            img_graphs = []
            world_graphs = []
            for frames_df in frames_df_list:
                curr_img = images[frames_df.clip_name.iloc[0]]["data"][frames_df.grabindex.iloc[0]][0][0]
                img_graphs.append(
                    draw_img(
                        curr_img,
                        frames_df,
                        frames_df.dump_name.iloc[0],
                        frames_df.clip_name.iloc[0],
                        frames_df.grabindex.iloc[0],
                    )
                )
                world_graphs.append(draw_top_view(frames_df))

            img_graphs[0].style["display"] = "block"
            world_graphs[0].style["display"] = "block"
            dump_row = dbc.Row(
                [dbc.Col(loading_wrapper(img_graphs), width=10), dbc.Col(loading_wrapper(world_graphs), width=2)]
            )
            final_layout.append(dump_row)

        return final_layout

    @staticmethod
    def parse_labels_df(labels_df: pd.DataFrame):
        if labels_df.empty:
            return {}

        labels_df = labels_df.map(FramesModal.safe_json)
        return labels_df

    @staticmethod
    def safe_json(x):
        try:
            return np.array(orjson.loads(x))
        except orjson.JSONDecodeError:
            return x
