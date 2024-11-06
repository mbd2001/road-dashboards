import dash_bootstrap_components as dbc
import numpy as np
import orjson
import pandas as pd
from dash import Input, Output, Patch, State, callback, callback_context, dcc, html, no_update, set_props
from pypika import EmptyCriterion
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

from road_dashboards.road_dump_dashboard.graphical_components.frame_drawer import draw_img, draw_top_view
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import (
    card_wrapper,
    loading_wrapper,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import diff_labels_subquery
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_with_dropdown import (
    ConfMatGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base, Column
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object, execute, load_object


class FramesModal(GridObject):
    IMG_LIMIT = 25

    def __init__(
        self,
        main_dataset_dropdown_id: str,
        secondary_dataset_dropdown_id: str,
        page_filters_id: str,
        main_table: str,
        triggering_conf_mats: list[ConfMatGraph] = None,
        triggering_dropdown_conf_mats: list[ConfMatGraphWithDropdown] = None,
        component_id: str = "",
    ):
        self.main_dataset_dropdown_id = main_dataset_dropdown_id
        self.secondary_dataset_dropdown_id = secondary_dataset_dropdown_id
        self.page_filters_id = page_filters_id
        self.main_table = main_table
        self.triggering_conf_mats = triggering_conf_mats
        self.triggering_dropdown_conf_mats = triggering_dropdown_conf_mats
        super().__init__(full_grid_row=True, component_id=component_id)

    def _generate_ids(self):
        self.curr_img_index_id = self._generate_id("curr_img_index")
        self.curr_drawn_column_id = self._generate_id("curr_drawn_column")
        self.curr_drawn_column_filter_id = self._generate_id("curr_drawn_column_filter")

        self.main_img_id = self._generate_id("main_img")
        self.main_world_id = self._generate_id("main_world")

        self.secondary_img_id = self._generate_id("secondary_img")
        self.secondary_world_id = self._generate_id("secondary_world")

        self.next_btn_id = self._generate_id("next_btn")
        self.prev_btn_id = self._generate_id("prev_btn")

    def layout(self):
        frames_layout = html.Div(
            id=self.component_id,
            children=[
                dcc.Store(id=self.curr_img_index_id, data=0),
                dcc.Store(id=self.curr_drawn_column_id),
                dcc.Store(id=self.curr_drawn_column_filter_id, data=dump_object(EmptyCriterion())),
                card_wrapper(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    loading_wrapper(
                                        html.Div(dcc.Graph(config={"displayModeBar": False}), id=self.main_world_id)
                                    ),
                                    width=1,
                                ),
                                dbc.Col(
                                    loading_wrapper(
                                        html.Div(dcc.Graph(config={"displayModeBar": False}), id=self.main_img_id)
                                    ),
                                    width=5,
                                ),
                                dbc.Col(
                                    loading_wrapper(
                                        html.Div(dcc.Graph(config={"displayModeBar": False}), id=self.secondary_img_id)
                                    ),
                                    width=5,
                                ),
                                dbc.Col(
                                    loading_wrapper(
                                        html.Div(
                                            dcc.Graph(config={"displayModeBar": False}), id=self.secondary_world_id
                                        )
                                    ),
                                    width=1,
                                ),
                            ],
                        ),
                        dbc.Row(
                            dbc.Stack(
                                [
                                    dbc.Button(
                                        "Prev Frame",
                                        id=self.prev_btn_id,
                                        className="bg-primary mt-5",
                                        color="secondary",
                                        style={"margin": "10px"},
                                    ),
                                    dbc.Button(
                                        "Next Frame",
                                        id=self.next_btn_id,
                                        className="bg-primary mt-5",
                                        color="secondary",
                                        style={"margin": "10px"},
                                    ),
                                ],
                                direction="horizontal",
                                gap=1,
                            )
                        ),
                    ]
                ),
            ],
            hidden=True,
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
                State(self.main_dataset_dropdown_id, "value"),
                State(self.secondary_dataset_dropdown_id, "value"),
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
                extra_columns = list(main_tables[0].get_columns(names_only=False, include_all_columns=True))
                query = diff_labels_subquery(
                    diff_column=conf_mat.column,
                    label_columns=extra_columns,
                    main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    data_filter=conf_mat.filter if filter_ignores else EmptyCriterion(),
                    page_filters=load_object(filters),
                    limit=self.IMG_LIMIT,
                )
                data = execute(query)
                main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = (
                    self.compute_images_from_query_data(data, extra_columns)
                )

                set_props(self.main_img_id, {"children": main_img_figs})
                set_props(self.main_world_id, {"children": main_world_figs})
                set_props(self.secondary_img_id, {"children": secondary_img_figs})
                set_props(self.secondary_world_id, {"children": secondary_world_figs})
                set_props(self.curr_img_index_id, {"data": 0})
                set_props(self.component_id, {"hidden": False})
                set_props(self.curr_drawn_column_id, {"data": dump_object(conf_mat.column)})
                set_props(self.curr_drawn_column_filter_id, {"data": dump_object(conf_mat.filter)})
                return filter_ignores

        for dropdown_conf_mat in self.triggering_dropdown_conf_mats:

            @callback(
                Output(self.main_img_id, "children", allow_duplicate=True),
                Output(self.main_world_id, "children", allow_duplicate=True),
                Output(self.secondary_img_id, "children", allow_duplicate=True),
                Output(self.secondary_world_id, "children", allow_duplicate=True),
                Output(self.curr_img_index_id, "data", allow_duplicate=True),
                Output(self.component_id, "hidden"),
                Output(self.curr_drawn_column_id, "data"),
                Output(self.curr_drawn_column_filter_id, "data"),
                State(self.page_filters_id, "data"),
                State(self.main_table, "data"),
                State(META_DATA, "data"),
                State(self.main_dataset_dropdown_id, "value"),
                State(self.secondary_dataset_dropdown_id, "value"),
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
                    return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables) if md_tables else None
                extra_columns = list(main_tables[0].get_columns(names_only=False))
                dynamic_column = load_object(dynamic_column)
                query = diff_labels_subquery(
                    diff_column=dynamic_column,
                    label_columns=extra_columns,
                    main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    page_filters=load_object(filters),
                    limit=self.IMG_LIMIT,
                )
                data = execute(query)
                main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = (
                    self.compute_images_from_query_data(data, extra_columns)
                )
                return (
                    main_img_figs,
                    main_world_figs,
                    secondary_img_figs,
                    secondary_world_figs,
                    0,
                    False,
                    dump_object(dynamic_column),
                    dump_object(EmptyCriterion()),
                )

        @callback(
            Output(self.main_img_id, "children"),
            Output(self.main_world_id, "children"),
            Output(self.secondary_img_id, "children"),
            Output(self.secondary_world_id, "children"),
            Output(self.curr_img_index_id, "data"),
            Input(self.page_filters_id, "data"),
            Input(self.main_table, "data"),
            Input(META_DATA, "data"),
            Input(self.main_dataset_dropdown_id, "value"),
            Input(self.secondary_dataset_dropdown_id, "value"),
            State(self.curr_drawn_column_id, "data"),
            State(self.curr_drawn_column_filter_id, "data"),
        )
        def draw_diffs_general_buttons_case(
            filters, main_tables, md_tables, main_dump, secondary_dump, column_to_compare, column_filter
        ):
            if not column_to_compare or not main_tables or not md_tables or not main_dump or not secondary_dump:
                return no_update, no_update, no_update, no_update, no_update

            main_tables: list[Base] = load_object(main_tables)
            md_tables: list[Base] = load_object(md_tables) if md_tables else None
            extra_columns = list(main_tables[0].get_columns(names_only=False))
            column_to_compare = load_object(column_to_compare)
            query = diff_labels_subquery(
                diff_column=column_to_compare,
                label_columns=extra_columns,
                main_labels=[table for table in main_tables if table.dataset_name == main_dump],
                secondary_labels=[table for table in main_tables if table.dataset_name == secondary_dump],
                main_md=[table for table in md_tables if table.dataset_name == main_dump],
                secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                data_filter=load_object(column_filter),
                page_filters=load_object(filters),
                limit=self.IMG_LIMIT,
            )
            data = execute(query)
            main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs = (
                self.compute_images_from_query_data(data, extra_columns)
            )
            return main_img_figs, main_world_figs, secondary_img_figs, secondary_world_figs, 0

        @callback(
            Output(self.main_img_id, "children", allow_duplicate=True),
            Output(self.main_world_id, "children", allow_duplicate=True),
            Output(self.secondary_img_id, "children", allow_duplicate=True),
            Output(self.secondary_world_id, "children", allow_duplicate=True),
            Output(self.curr_img_index_id, "data", allow_duplicate=True),
            Input(self.curr_img_index_id, "data"),
            Input(self.prev_btn_id, "n_clicks"),
            Input(self.next_btn_id, "n_clicks"),
            prevent_initial_call=True,
        )
        def update_frame_graphs(
            ind,
            prev_n_clicks,
            next_n_clicks,
        ):
            triggered_id = callback_context.triggered_id
            if not triggered_id or ind is None:
                return no_update, no_update, no_update, no_update, no_update

            main_img = Patch()
            main_world = Patch()
            secondary_img = Patch()
            secondary_world = Patch()
            if triggered_id != self.curr_img_index_id:
                n_clicks = callback_context.triggered[0]["value"]
                if n_clicks == 0:
                    return no_update, no_update, no_update, no_update, no_update

                main_img[ind]["props"]["style"]["display"] = "none"
                main_world[ind]["props"]["style"]["display"] = "none"
                secondary_img[ind]["props"]["style"]["display"] = "none"
                secondary_world[ind]["props"]["style"]["display"] = "none"

                if triggered_id == self.prev_btn_id:
                    ind = (ind - 1) % self.IMG_LIMIT
                elif triggered_id == self.next_btn_id:
                    ind = (ind + 1) % self.IMG_LIMIT

            main_img[ind]["props"]["style"]["display"] = "block"
            main_world[ind]["props"]["style"]["display"] = "block"
            secondary_img[ind]["props"]["style"]["display"] = "block"
            secondary_world[ind]["props"]["style"]["display"] = "block"
            return (
                main_img,
                main_world,
                secondary_img,
                secondary_world,
                ind if triggered_id != self.curr_img_index_id else no_update,
            )

    @staticmethod
    def compute_images_from_query_data(data, extra_columns):
        labels_df = FramesModal.parse_labels_df(data, extra_columns)

        indexes_df = labels_df[["clip_name", "grabindex"]].drop_duplicates()
        clip_names = indexes_df.clip_name
        grab_indexes = [int(gi) for gi in indexes_df.grabindex]
        data_types = ["data"] * len(clip_names)
        images = DroneViewDBManager.load_multiple_clips_images(clip_names, grab_indexes, data_types)

        dumps_df_list = [d for _, d in labels_df.groupby(["dump_name"])]
        img_figs = [[] for _ in range(len(dumps_df_list))]
        world_figs = [[] for _ in range(len(dumps_df_list))]
        for dump_df, img_fig, world_fig in zip(dumps_df_list, img_figs, world_figs):
            frames_df_list = [i for _, i in dump_df.groupby(["clip_name", "grabindex"])]
            for frames_df in frames_df_list:
                curr_img = images[frames_df.clip_name.iloc[0]]["data"][frames_df.grabindex.iloc[0]][0][0]
                img_fig.append(
                    draw_img(
                        curr_img,
                        frames_df,
                        frames_df.dump_name.iloc[0],
                        frames_df.clip_name.iloc[0],
                        frames_df.grabindex.iloc[0],
                    )
                )
                world_fig.append(draw_top_view(frames_df))

        return img_figs[0], world_figs[0], img_figs[1], world_figs[1]

    @staticmethod
    def parse_labels_df(labels_df: pd.DataFrame, extra_columns: list[Column]):
        if labels_df.empty:
            return {}

        arr_columns = [col.alias for col in extra_columns]
        labels_df[arr_columns] = labels_df[arr_columns].map(FramesModal.safe_json).map(np.array)
        return labels_df

    @staticmethod
    def safe_json(x):
        try:
            return orjson.loads(x)
        except orjson.JSONDecodeError:
            return x
