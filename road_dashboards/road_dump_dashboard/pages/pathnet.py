from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import page_header
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import Column
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_with_dropdown import ConfMatGraphWithDropdown
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph import GroupByGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph_with_dropdown import (
    GroupByGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_generator import grid_layout

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
    GroupByGraph(title="Role Distribution", columns=[Column("dp_role")]),
    GroupByGraph(
        title="Split Role Distribution",
        columns=[Column("dp_split_role")],
        filter="dp_split_role <> 'IGNORE'",
    ),
    GroupByGraph(
        title="Primary Role Distribution",
        columns=[Column("dp_primary_role")],
        filter="dp_primary_role <> 'IGNORE'",
    ),
    GroupByGraph(
        title="Merge Role Distribution",
        columns=[Column("dp_merge_role")],
        filter="dp_merge_role <> 'IGNORE'",
    ),
    GroupByGraph(title="Oncoming Distribution", columns=[Column("dp_points_oncoming")]),
    GroupByGraph(title="Batch Distribution", columns=[Column("batch_num")], full_grid_row=True),
    GroupByGraphWithDropdown(),
]

conf_mat_graphs = [
    ConfMatGraph(title="Role Classification", column=Column("dp_role"), full_grid_row=True),
    ConfMatGraph(
        title="Split Role Classification",
        column=Column("dp_split_role"),
        filter="dp_split_role <> 'IGNORE'",
    ),
    ConfMatGraph(
        title="Primary Role Classification",
        column=Column("dp_primary_role"),
        filter="dp_primary_role <> 'IGNORE'",
    ),
    ConfMatGraph(
        title="Merge Role Classification",
        column=Column("dp_merge_role"),
        filter="dp_merge_role <> 'IGNORE'",
    ),
    ConfMatGraph(title="Oncoming Classification", column=Column("dp_points_oncoming")),
    ConfMatGraphWithDropdown(),
]

layout = html.Div(
    [
        page_header.layout(page_properties.title),
        grid_layout(group_by_graphs),
        conf_mats_collection.layout(conf_mat_graphs),
    ]
)
