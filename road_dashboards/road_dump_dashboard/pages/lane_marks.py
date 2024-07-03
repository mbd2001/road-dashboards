from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import GRAPHS_PER_PAGE
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

page_graphs = GRAPHS_PER_PAGE.get(page_properties.path.strip("/"))
count_graphs = page_graphs.get("count_graphs")
conf_mat_graphs = page_graphs.get("conf_mat_graphs")
layout = html.Div(
    [
        html.H1(page_properties.title, className="mb-5"),
        data_filters.layout,
        base_dataset_statistics.layout(page_properties.objs_name),
        count_graphs_collection.layout(count_graphs, True),
        conf_mats_collection.layout(conf_mat_graphs),
    ]
)
