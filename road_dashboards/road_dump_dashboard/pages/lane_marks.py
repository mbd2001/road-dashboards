from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import page_header
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import (
    ArrayColumn,
    NumericColumn,
    StringColumn,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_with_dropdown import ConfMatGraphWithDropdown
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph import GroupByGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph_with_dropdown import (
    GroupByGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_generator import grid_layout
from road_dashboards.road_dump_dashboard.components.grid_objects.obj_count_graph import ObjCountGraph

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

count_graphs = [
    GroupByGraph(
        title="Type Distribution",
        columns=[StringColumn("type")],
        full_grid_row=True,
    ),
    GroupByGraph(
        title="Color Distribution",
        columns=[StringColumn("color")],
    ),
    GroupByGraph(
        title="Role Distribution",
        columns=[StringColumn("role")],
    ),
    GroupByGraph(
        title="Max View Range Distribution (m)",
        columns=[NumericColumn("max_view_range")],
        slider_value=0,
        full_grid_row=True,
        filter="max_view_range < 250",
    ),
    GroupByGraph(
        title="Dashed Painted Length Distribution",
        columns=[ArrayColumn("dashed_length", filter="BETWEEN 0 AND 20", unnest=True)],
        slider_value=1,
        full_grid_row=True,
        filter="type = 'dashed'",
    ),
    GroupByGraph(
        title="Dashed Gap Length Distribution",
        columns=[ArrayColumn("dashed_gap", filter="BETWEEN 0 AND 25", unnest=True)],
        slider_value=1,
        full_grid_row=True,
        filter="type = 'dashed'",
    ),
    GroupByGraph(
        title="Lane Mark Width Distribution (m)",
        columns=[NumericColumn("avg_lm_width")],
        slider_value=2,
        full_grid_row=True,
        filter="avg_lm_width > 0 AND avg_lm_width < 1.5",
    ),
    GroupByGraph(
        title="Batch Distribution",
        columns=[NumericColumn("batch_num")],
        full_grid_row=True,
    ),
    ObjCountGraph(),
    GroupByGraphWithDropdown(),
]

conf_mat_graphs = [
    ConfMatGraph(title="Type Classification", column=StringColumn("type"), full_grid_row=True),
    ConfMatGraph(title="Role Classification", column=StringColumn("role")),
    ConfMatGraph(title="Color Classification", column=StringColumn("color")),
    ConfMatGraphWithDropdown(),
]

layout = html.Div(
    [
        page_header.layout(page_properties.title),
        grid_layout(count_graphs),
        conf_mats_collection.layout(conf_mat_graphs),
    ]
)
