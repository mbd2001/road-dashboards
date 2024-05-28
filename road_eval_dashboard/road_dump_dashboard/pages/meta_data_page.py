from dash import html, register_page

from road_eval_dashboard.road_dump_dashboard import PageProperties
from road_eval_dashboard.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_eval_dashboard.road_dump_dashboard.components.graph_wrappers import (
    bar_pie_graphs_collection,
    conf_mats_collection,
    countries_heatmap,
)

page_properties = PageProperties(icon="search", path="/meta_data", name="Meta Data")
register_page(__name__, order=1, **page_properties.__dict__)


layout = html.Div(
    [
        html.H1(page_properties.name, className="mb-5"),
        data_filters.layout(main_table="meta_data"),
        base_dataset_statistics.layout(objs_name="frames", main_table="meta_data"),
        bar_pie_graphs_collection.layout(
            main_table="meta_data",
            columns=["is_tv_perfect", "gtem_labels_exist", "batch_num"],
            filters=["road_type", "lane_mark_color"],
        ),
        conf_mats_collection.layout(main_table="meta_data", columns_to_compare=["is_tv_perfect", "gtem_labels_exist"]),
        countries_heatmap.layout,
    ]
)
