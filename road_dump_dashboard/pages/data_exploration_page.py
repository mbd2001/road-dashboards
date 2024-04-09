from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout import data_filters, base_dataset_statistics
from road_dump_dashboard.components.graph_wrappers import countries_heatmap
from road_dump_dashboard.components.graph_wrappers import conf_mats_collection
from road_dump_dashboard.components.graph_wrappers import bar_pie_graphs_collection
from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

page_properties = PageProperties(icon="search", path="/data_exploration", name="Data Exploration")
register_page(__name__, order=1, **page_properties.__dict__)


layout = html.Div(
    [
        html.H1(page_properties.name, className="mb-5"),
        data_filters.layout(main_table="meta_data"),
        base_dataset_statistics.layout(objs_name="frames", main_table="meta_data"),
        bar_pie_graphs_collection.layout(
            main_table="meta_data", columns=["is_tv_perfect", "gtem_labels_exist"], filters=["road_type", "lane_mark"]
        ),
        conf_mats_collection.layout(main_table="meta_data", columns_to_compare=["is_tv_perfect", "gtem_labels_exist"]),
        countries_heatmap.layout,
    ]
)
