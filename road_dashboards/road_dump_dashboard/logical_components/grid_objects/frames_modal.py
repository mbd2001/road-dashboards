import dash_bootstrap_components as dbc
import numpy as np
import orjson
import pandas as pd
from dash import Input, Output, Patch, State, callback, callback_context, clientside_callback, dcc, html, no_update
from pypika import Criterion, EmptyCriterion, Query, Tuple
from pypika.queries import QueryBuilder
from pypika.terms import Term
from road_database_toolkit.dynamo_db.drone_view_images.db_manager import DroneViewDBManager

from road_dashboards.road_dump_dashboard.graphical_components.frame_drawer import draw_img, draw_top_view
from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import META_DATA
from road_dashboards.road_dump_dashboard.logical_components.constants.layout_wrappers import loading_wrapper
from road_dashboards.road_dump_dashboard.logical_components.constants.query_abstractions import (
    base_data_subquery,
    diff_terms_subquery,
    union_all_query_list,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.data_filters import DataFilters
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.grid_object import GridObject
from road_dashboards.road_dump_dashboard.table_schemes.base import Base
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import (
    dump_object,
    execute,
    load_object,
    optional_inputs,
)
from road_dashboards.road_dump_dashboard.table_schemes.meta_data import MetaData


class FramesModal(GridObject):
    IMG_LIMIT: int = 64

    def __init__(
        self,
        page_filters_id: str = "",
        triggering_conf_mats: list[ConfMatGraph] | None = None,
        triggering_filters: list[DataFilters] | None = None,
        component_id: str = "",
    ):
        self.page_filters_id = page_filters_id
        self.triggering_conf_mats = triggering_conf_mats if triggering_conf_mats else []
        self.triggering_filters = triggering_filters if triggering_filters else []
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
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                Input(conf_mat.show_diff_btn_id, "n_clicks"),
                State(conf_mat.filter_ignores_btn_id, "on"),
                State(conf_mat.main_table, "data"),
                State(META_DATA, "data"),
                State(conf_mat.main_dataset_dropdown_id, "value"),
                State(conf_mat.secondary_dataset_dropdown_id, "value"),
                optional_inputs(
                    page_filters=State(conf_mat.page_filters_id, "data"),
                    column=State(conf_mat.columns_dropdown_id, "value"),
                ),
                prevent_initial_call=True,
            )
            def draw_diffs_generic_case(
                show_diff_n_clicks,
                filter_ignores,
                main_tables,
                md_tables,
                main_dump,
                secondary_dump,
                optional,
                column=conf_mat.column,
                filter=conf_mat.filter,
            ):
                if not show_diff_n_clicks or not main_tables:
                    return no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                column: Term = column or getattr(type(main_tables[0]), optional["column"], None)
                if not column:
                    return no_update

                md_tables: list[Base] = load_object(md_tables)
                page_filters: str = optional.get("page_filters", None)
                page_filters: Criterion = load_object(page_filters) if page_filters else EmptyCriterion()
                extra_columns = list(
                    type(main_tables[0]).get_columns(names_only=False, include_list_columns=True, only_drawable=True)
                )
                query = self.diff_labels_subquery(
                    main_tables=[table for table in main_tables if table.dataset_name == main_dump],
                    secondary_tables=[table for table in main_tables if table.dataset_name == secondary_dump],
                    main_md=[table for table in md_tables if table.dataset_name == main_dump],
                    secondary_md=[table for table in md_tables if table.dataset_name == secondary_dump],
                    label_columns=extra_columns,
                    diff_column=column,
                    data_filter=filter if filter_ignores else EmptyCriterion(),
                    page_filters=page_filters,
                    limit=self.IMG_LIMIT,
                )
                return dump_object(query), True

        for triggering_filter in self.triggering_filters:

            @callback(
                Output(self.curr_query_id, "data", allow_duplicate=True),
                Output(self.component_id, "is_open", allow_duplicate=True),
                Input(triggering_filter.show_n_frames_btn_id, "n_clicks"),
                State(self.page_filters_id, "data"),
                State(triggering_filter.main_table, "data"),
                State(META_DATA, "data"),
                prevent_initial_call=True,
            )
            def draw_general_data_case(
                n_clicks,
                filters,
                main_tables,
                md_tables,
            ):
                if not n_clicks or not main_tables:
                    return no_update, no_update

                main_tables: list[Base] = load_object(main_tables)
                md_tables: list[Base] = load_object(md_tables)
                extra_columns = list(
                    type(main_tables[0]).get_columns(names_only=False, include_list_columns=True, only_drawable=True)
                )
                query = self.general_labels_subquery(
                    main_tables=main_tables,
                    meta_data_tables=md_tables,
                    label_columns=extra_columns,
                    page_filters=load_object(filters),
                    limit=self.IMG_LIMIT,
                )
                return dump_object(query), True

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
            num_of_drawn_datasets,
        ):
            images_layout = Patch()
            n_clicks = callback_context.triggered[0]["value"]
            if n_clicks == 0:
                return no_update, no_update

            self.edit_display_of_images_in_each_layout_row(images_layout, num_of_drawn_datasets, img_ind, "none")
            triggered_id = callback_context.triggered_id
            if triggered_id == self.prev_btn_id:
                img_ind = (img_ind - 1) % self.IMG_LIMIT
            elif triggered_id == self.next_btn_id:
                img_ind = (img_ind + 1) % self.IMG_LIMIT

            self.edit_display_of_images_in_each_layout_row(images_layout, num_of_drawn_datasets, img_ind, "block")
            return images_layout, img_ind

    @staticmethod
    def edit_display_of_images_in_each_layout_row(
        images_layout: Patch, num_of_drawn_datasets: int, img_ind: int, display: str
    ):
        for dataset_ind in range(num_of_drawn_datasets):
            images_layout[dataset_ind]["props"]["children"][0]["props"]["children"]["props"]["children"][img_ind][
                "props"
            ]["style"]["display"] = display
            images_layout[dataset_ind]["props"]["children"][1]["props"]["children"]["props"]["children"][img_ind][
                "props"
            ]["style"]["display"] = display

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

    @staticmethod
    def diff_labels_subquery(
        main_tables: list[Base],
        secondary_tables: list[Base],
        main_md: list[Base],
        secondary_md: list[Base],
        label_columns: list[Term],
        diff_column: Term,
        data_filter: Criterion = EmptyCriterion(),
        page_filters: Criterion = EmptyCriterion(),
        limit: int | None = None,
    ) -> QueryBuilder:
        diff_terms = diff_terms_subquery(
            main_tables=main_tables,
            secondary_tables=secondary_tables,
            main_md=main_md,
            secondary_md=secondary_md,
            diff_column=diff_column,
            data_filter=data_filter,
            page_filters=page_filters,
        )
        ids_subquery = (
            Query.from_(diff_terms).select(diff_terms.clip_name, diff_terms.grabindex).distinct().limit(limit)
        )

        terms = list({*label_columns})
        labels_queries = [
            base_data_subquery(
                main_tables=main_table,
                meta_data_tables=md_table,
                terms=terms,
                data_filter=data_filter,
                page_filters=page_filters,
            )
            for main_table, md_table in [[main_tables, main_md], [secondary_tables, secondary_md]]
        ]
        union_query = union_all_query_list(labels_queries)
        labels_query = (
            Query.from_(union_query)
            .where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(ids_subquery))
            .select(*terms)
        )
        return labels_query

    @staticmethod
    def general_labels_subquery(
        main_tables: list[Base],
        meta_data_tables: list[Base],
        label_columns: list[Term],
        data_filter: Criterion = EmptyCriterion(),
        page_filters: Criterion = EmptyCriterion(),
        limit: int | None = None,
    ) -> QueryBuilder:
        ids_terms = [MetaData.clip_name, MetaData.grabindex]
        ids_query = base_data_subquery(
            main_tables=main_tables,
            meta_data_tables=meta_data_tables,
            terms=ids_terms,
            data_filter=data_filter,
            page_filters=page_filters,
            intersection_on=True,
        )
        ids_subquery = Query.from_(ids_query).select(ids_query.clip_name, ids_query.grabindex).distinct().limit(limit)

        terms = list({*label_columns})
        labels_query = base_data_subquery(
            main_tables=main_tables,
            meta_data_tables=meta_data_tables,
            terms=terms,
            data_filter=data_filter,
            page_filters=page_filters,
            intersection_on=True,
        )
        final_query = (
            Query.from_(labels_query)
            .where(Tuple(MetaData.clip_name, MetaData.grabindex).isin(ids_subquery))
            .select(*terms)
        )
        return final_query
