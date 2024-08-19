from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import ArrayColumn, BaseColumn
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
        group_by_column=BaseColumn("type"),
        full_grid_row=True,
    ),
    GroupByGraphProperties(
        name="Role Distribution",
        group_by_column=BaseColumn("role"),
    ),
    GroupByGraphProperties(
        name="Color Distribution",
        group_by_column=BaseColumn("color"),
    ),
    GroupByGraphProperties(
        name="Max View Range Distribution (m)",
        group_by_column=BaseColumn("max_view_range"),
        include_slider=True,
        slider_default_value=0,
        full_grid_row=True,
        ignore_filter="max_view_range < 250",
    ),
    GroupByGraphProperties(
        name="Dashed Painted Length Distribution",
        group_by_column=ArrayColumn("dashed_length", filter="BETWEEN 0 AND 20", unnest=True),
        include_slider=True,
        slider_default_value=-1,
        full_grid_row=True,
        ignore_filter="type = 'dashed'",
    ),
    GroupByGraphProperties(
        name="Dashed Gap Length Distribution",
        group_by_column=ArrayColumn("dashed_gap", filter="BETWEEN 0 AND 25", unnest=True),
        include_slider=True,
        slider_default_value=-1,
        full_grid_row=True,
        ignore_filter="type = 'dashed'",
    ),
    GroupByGraphProperties(
        name="Lane Mark Width Distribution (m)",
        group_by_column=BaseColumn("avg_lm_width"),
        include_slider=True,
        slider_default_value=-2,
        ignore_filter="avg_lm_width > 0 AND avg_lm_width < 1.5",
        full_grid_row=True,
    ),
    GroupByGraphProperties(name="Batch Distribution", group_by_column=BaseColumn("batch_num"), full_grid_row=True),
]

conf_mat_graphs = [
    ConfMatGraphProperties(name="Role Classification", column_to_compare=BaseColumn("role")),
    ConfMatGraphProperties(name="Color Classification", column_to_compare=BaseColumn("color")),
    ConfMatGraphProperties(name="Type Classification", column_to_compare=BaseColumn("type")),
]

layout = html.Div(
    [
        html.H1(page_properties.title, className="mb-5"),
        data_filters.layout,
        base_dataset_statistics.layout(),
        count_graphs_collection.layout(group_by_graphs, draw_obj_count=True),
        conf_mats_collection.layout(conf_mat_graphs),
    ]
)
