from dash import register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout import page_header
from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.constants.columns_properties import (
    BoolColumn,
    Case,
    NumericColumn,
    StringColumn,
)
from road_dashboards.road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dashboards.road_dump_dashboard.components.graph_wrappers import conf_mats_collection
from road_dashboards.road_dump_dashboard.components.grid_objects.cases_graph import CasesGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_graph import ConfMatGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.conf_mat_with_dropdown import ConfMatGraphWithDropdown
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph import GroupByGraph
from road_dashboards.road_dump_dashboard.components.grid_objects.count_graph_with_dropdown import (
    GroupByGraphWithDropdown,
)
from road_dashboards.road_dump_dashboard.components.grid_objects.countries_heatmap import CountriesHeatMap
from road_dashboards.road_dump_dashboard.components.grid_objects.grid_generator import grid_layout

page_properties = PageProperties(
    order=1,
    icon="search",
    path="/meta_data",
    title="Meta Data",
    objs_name="frames",
    main_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)


count_graphs = [
    GroupByGraph(title="Top View Perfects Exists", columns=[BoolColumn("gtem_labels_exist")]),
    GroupByGraph(
        title="Gtem Exists",
        columns=[BoolColumn("gtem_labels_exist")],
    ),
    GroupByGraph(
        title="Curve Rad Distribution",
        columns=[NumericColumn("curve_rad_ahead")],
        slider_value=-2,
        filter="curve_rad_ahead <> 99999",
        full_grid_row=True,
    ),
    GroupByGraph(
        title="Batch Distribution",
        columns=[NumericColumn("batch_num")],
        full_grid_row=True,
    ),
    CasesGraph(
        title="Road Type Distribution",
        cases=[
            Case(name="highway", filter="mdbi_road_highway = TRUE", extra_columns=[StringColumn("mdbi_road_highway")]),
            Case(name="country", filter="mdbi_road_country = TRUE", extra_columns=[StringColumn("mdbi_road_country")]),
            Case(name="urban", filter="mdbi_road_city = TRUE", extra_columns=[StringColumn("mdbi_road_city")]),
            Case(name="freeway", filter="mdbi_road_freeway = TRUE", extra_columns=[StringColumn("mdbi_road_freeway")]),
        ],
    ),
    CasesGraph(
        title="Lane Mark Color Distribution",
        cases=[
            Case(
                name="yellow",
                filter="rightColor_yellow = TRUE OR leftColor_yellow = TRUE",
                extra_columns=[StringColumn("rightColor_yellow"), StringColumn("leftColor_yellow")],
            ),
            Case(
                name="white",
                filter="rightColor_white = TRUE OR leftColor_white = TRUE",
                extra_columns=[StringColumn("rightColor_white"), StringColumn("leftColor_white")],
            ),
            Case(
                name="blue",
                filter="rightColor_blue = TRUE OR leftColor_blue = TRUE",
                extra_columns=[StringColumn("rightColor_blue"), StringColumn("leftColor_blue")],
            ),
        ],
    ),
    GroupByGraphWithDropdown(),
]

conf_mat_graphs = [
    ConfMatGraph(
        title="Top View Perfects Classification",
        column=BoolColumn("is_tv_perfect"),
    ),
    ConfMatGraph(title="Gtem Classification", column=BoolColumn("gtem_labels_exist")),
    ConfMatGraphWithDropdown(),
]


layout = [
    page_header.layout(page_properties.title),
    grid_layout(count_graphs),
    conf_mats_collection.layout(conf_mat_graphs),
    card_wrapper(CountriesHeatMap().layout()),
]
