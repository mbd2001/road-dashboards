from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dump_dashboard.components.graph_wrappers import bar_pie_graphs_collection

page_properties = PageProperties("search", path="/lane_marks", name="Lane Marks")
register_page(__name__, order=2, **page_properties.__dict__)

layout = html.Div(
    [
        html.H1(page_properties.name, className="mb-5"),
        data_filters.layout(main_table="lm_meta_data", meta_data_table="meta_data"),
        base_dataset_statistics.layout(objs_name="lane marks", main_table="lm_meta_data", meta_data_table="meta_data"),
        bar_pie_graphs_collection.layout(
            main_table="lm_meta_data",
            meta_data_table="meta_data",
            columns=[
                "role",
                "color",
                "type",
                "view_range",
                "lane_mark_width",
                "dashed_length",
            ],  # TODO: add 'dashed_gap'
        ),
    ]
)
