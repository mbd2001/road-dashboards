from dash import html, register_page

from road_eval_dashboard.road_dump_dashboard import PageProperties
from road_eval_dashboard.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_eval_dashboard.road_dump_dashboard.components.graph_wrappers import (
    bar_pie_graphs_collection,
    conf_mats_collection,
)

page_properties = PageProperties("search", path="/pathnet", name="Pathnet")
register_page(__name__, order=3, **page_properties.__dict__)

layout = html.Div(
    [
        html.H1(page_properties.name, className="mb-5"),
        data_filters.layout(main_table="rpw_meta_data", meta_data_table="meta_data"),
        base_dataset_statistics.layout(objs_name="DPs", main_table="rpw_meta_data", meta_data_table="meta_data"),
        bar_pie_graphs_collection.layout(
            main_table="rpw_meta_data",
            meta_data_table="meta_data",
            columns=["dp_role", "dp_split_role", "dp_primary_role", "dp_merge_role", "dp_points_oncoming", "batch_num"],
        ),
        conf_mats_collection.layout(
            main_table="rpw_meta_data",
            meta_data_table="meta_data",
            columns_to_compare=["dp_role", "dp_split_role", "dp_primary_role", "dp_merge_role", "dp_points_oncoming"],
        ),
    ]
)
