from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BaseColumn
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import (
    ConfMatGraphProperties,
    GroupByGraphProperties,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection, count_graphs_collection

page_properties = PageProperties(
    order=3,
    icon="search",
    path="/pathnet",
    title="Pathnet",
    objs_name="DPs",
    main_table="rpw_meta_data",
    meta_data_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)

group_by_graphs = [
    GroupByGraphProperties(name="Role Distribution", group_by_column=BaseColumn("dp_role")),
    GroupByGraphProperties(
        name="Split Role Distribution",
        group_by_column=BaseColumn("dp_split_role"),
        ignore_filter="dp_split_role <> 'IGNORE'",
    ),
    GroupByGraphProperties(
        name="Primary Role Distribution",
        group_by_column=BaseColumn("dp_primary_role"),
        ignore_filter="dp_primary_role <> 'IGNORE'",
    ),
    GroupByGraphProperties(
        name="Merge Role Distribution",
        group_by_column=BaseColumn("dp_merge_role"),
        ignore_filter="dp_merge_role <> 'IGNORE'",
    ),
    GroupByGraphProperties(name="Oncoming Distribution", group_by_column=BaseColumn("dp_points_oncoming")),
    GroupByGraphProperties(name="Batch Distribution", group_by_column=BaseColumn("batch_num"), full_grid_row=True),
]

conf_mat_graphs = [
    ConfMatGraphProperties(name="Role Classification", column_to_compare=BaseColumn("dp_role"), full_grid_row=True),
    ConfMatGraphProperties(
        name="Split Role Classification",
        column_to_compare=BaseColumn("dp_split_role"),
        ignore_filter="dp_split_role <> 'IGNORE'",
    ),
    ConfMatGraphProperties(
        name="Primary Role Classification",
        column_to_compare=BaseColumn("dp_primary_role"),
        ignore_filter="dp_primary_role <> 'IGNORE'",
    ),
    ConfMatGraphProperties(
        name="Merge Role Classification",
        column_to_compare=BaseColumn("dp_merge_role"),
        ignore_filter="dp_merge_role <> 'IGNORE'",
    ),
    ConfMatGraphProperties(name="Oncoming Classification", column_to_compare=BaseColumn("dp_points_oncoming")),
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
