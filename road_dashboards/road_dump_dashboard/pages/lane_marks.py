from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import (
    ConfMatGraphProperties,
    GroupByGraphProperties,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection, count_graphs_collection

page_properties = PageProperties(
    order=2,
    icon="search",
    path="/lane_marks",
    title="Lane Marks",
    objs_name="lane marks",
    main_table="lm_meta_data",
    meta_data_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)


group_by_graphs = [
    GroupByGraphProperties(
        name="Type Distribution",
        group_by_column="type",
        full_grid_row=True,
    ),
    GroupByGraphProperties(
        name="Role Distribution",
        group_by_column="role",
    ),
    GroupByGraphProperties(
        name="Color Distribution",
        group_by_column="color",
    ),
    GroupByGraphProperties(
        name="Max View Range Distribution (m)",
        group_by_column="max_view_range",
        include_slider=True,
        slider_default_value=0,
        full_grid_row=True,
        ignore_filter="max_view_range < 250",
    ),
    GroupByGraphProperties(
        name="Dashed Length Distribution",
        group_by_column="dashed_length",
        include_slider=True,
        slider_default_value=0,
        ignore_filter="type LIKE '%ashed%'",
    ),
    GroupByGraphProperties(
        name="Dashed Gap Distribution",
        group_by_column="dashed_gap",
        include_slider=True,
        slider_default_value=0,
        ignore_filter="type LIKE '%ashed%'",
    ),
    GroupByGraphProperties(
        name="Lane Mark Width Distribution (m)",
        group_by_column="avg_lm_width",
        include_slider=True,
        slider_default_value=-2,
        ignore_filter="avg_lm_width BETWEEN 0 AND 1.5",
        full_grid_row=True,
    ),
    GroupByGraphProperties(name="Batch Distribution", group_by_column="batch_num", full_grid_row=True),
]

conf_mat_graphs = [
    ConfMatGraphProperties(name="Role Classification", column_to_compare="role"),
    ConfMatGraphProperties(name="Color Classification", column_to_compare="color"),
    ConfMatGraphProperties(name="Type Classification", column_to_compare="type"),
]

layout = html.Div(
    [
        html.H1(page_properties.title, className="mb-5"),
        data_filters.layout,
        base_dataset_statistics.layout(page_properties.objs_name),
        count_graphs_collection.layout(group_by_graphs, draw_obj_count=True),
        conf_mats_collection.layout(conf_mat_graphs),
    ]
)
