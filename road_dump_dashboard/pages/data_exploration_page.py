from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout import meta_data_filter, base_dataset_statistics
from road_dump_dashboard.components.graph_wrappers import countries_heatmap
from road_dump_dashboard.components.graph_wrappers import conf_mats_collection
from road_dump_dashboard.components.graph_wrappers import bar_graphs_collection
from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

extra_properties = PageProperties("search")
register_page(__name__, path="/data_exploration", name="Data Exploration", order=1, **extra_properties.__dict__)


def exponent_transform(value, base=10):
    return base**value


layout = html.Div(
    [
        html.H1("Data Exploration", className="mb-5"),
        meta_data_filter.layout("meta_data"),
        base_dataset_statistics.frame_layout,
        bar_graphs_collection.layout(
            columns=["is_tv_perfect", "gtem_labels_exist"], filters=["road_type", "lane_mark"]
        ),
        conf_mats_collection.layout(columns_to_compare=["is_tv_perfect", "gtem_labels_exist"]),
        countries_heatmap.layout,
    ]
)
