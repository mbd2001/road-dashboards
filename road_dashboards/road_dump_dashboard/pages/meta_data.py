from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import base_dataset_statistics, data_filters
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import BaseColumn
from road_dashboards.road_dump_dashboard.components.constants.graphs_properties import (
    CasesGraphProperties,
    ConfMatGraphProperties,
    GroupByGraphProperties,
)
from road_dashboards.road_dump_dashboard.components.graph_wrappers import (
    conf_mats_collection,
    count_graphs_collection,
    countries_heatmap,
)

page_properties = PageProperties(
    order=1,
    icon="search",
    path="/meta_data",
    title="Meta Data",
    objs_name="frames",
    main_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)


group_by_graphs = [
    GroupByGraphProperties(
        name="Top View Perfects Exists",
        group_by_column=BaseColumn("is_tv_perfect"),
    ),
    GroupByGraphProperties(
        name="Gtem Exists",
        group_by_column=BaseColumn("gtem_labels_exist"),
    ),
    GroupByGraphProperties(
        name="Curve Rad Distribution",
        group_by_column=BaseColumn("curve_rad_ahead"),
        full_grid_row=True,
        include_slider=True,
        slider_default_value=2,
        ignore_filter="curve_rad_ahead <> 99999",
    ),
    GroupByGraphProperties(name="Batch Distribution", group_by_column=BaseColumn("batch_num"), full_grid_row=True),
]

cases_graphs = [
    CasesGraphProperties(
        name="Road Type Distribution",
        interesting_cases={
            "highway": "mdbi_road_highway = TRUE",
            "country": "mdbi_road_country = TRUE",
            "urban": "mdbi_road_city = TRUE",
            "freeway": "mdbi_road_freeway = TRUE",
        },
        extra_columns=[
            BaseColumn("mdbi_road_highway"),
            BaseColumn("mdbi_road_country"),
            BaseColumn("mdbi_road_city"),
            BaseColumn("mdbi_road_freeway"),
        ],
    ),
    CasesGraphProperties(
        name="Lane Mark Color Distribution",
        interesting_cases={
            "yellow": "rightColor_yellow = TRUE OR leftColor_yellow = TRUE",
            "white": "rightColor_white = TRUE OR leftColor_white = TRUE",
            "blue": "rightColor_blue = TRUE OR leftColor_blue = TRUE",
        },
        extra_columns=[
            BaseColumn("rightColor_yellow"),
            BaseColumn("leftColor_yellow"),
            BaseColumn("rightColor_white"),
            BaseColumn("leftColor_white"),
            BaseColumn("rightColor_blue"),
            BaseColumn("leftColor_blue"),
        ],
    ),
]

conf_mat_graphs = [
    ConfMatGraphProperties(name="Top View Perfects Classification", column_to_compare=BaseColumn("is_tv_perfect")),
    ConfMatGraphProperties(name="Gtem Classification", column_to_compare=BaseColumn("gtem_labels_exist")),
]


layout = html.Div(
    [
        html.H1(page_properties.title, className="mb-5"),
        data_filters.layout,
        base_dataset_statistics.layout(),
        count_graphs_collection.layout(group_by_graphs, cases_graphs, draw_obj_count=False),
        conf_mats_collection.layout(conf_mat_graphs),
        countries_heatmap.layout(),
    ]
)
