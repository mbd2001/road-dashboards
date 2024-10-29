from dash import Input, Output, callback, dcc, html, register_page

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.pathnet_filters.layout import layout as pathnet_filters_card
from road_dashboards.road_eval_dashboard.pages.pathnet_page.tabs.boundaries_tab import boundaries_layout
from road_dashboards.road_eval_dashboard.pages.pathnet_page.tabs.positional_tab import pos_layout
from road_dashboards.road_eval_dashboard.pages.pathnet_page.tabs.quality_tab import quality_layout
from road_dashboards.road_eval_dashboard.pages.pathnet_page.tabs.roles_tab import role_layout

ACC_TAB_NAME = "pathnet-accuracy"
ROLE_TAB_NAME = "pathnet-roles"
QUALITY_TAB_NAME = "pathnet-quality-score"
BOUNDARIES_TAB_NAME = "pathnet-boundaries"

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/path_net", name="Path Net", order=9, **extra_properties.__dict__)

TABS_LAYOUTS = {
    ACC_TAB_NAME: pos_layout,
    ROLE_TAB_NAME: role_layout,
    QUALITY_TAB_NAME: quality_layout,
    BOUNDARIES_TAB_NAME: boundaries_layout,
}

layout = html.Div(
    [
        html.H1("Path Net Metrics", className="mb-5"),
        meta_data_filter.layout,
        pathnet_filters_card,
        base_dataset_statistics.dp_layout,
        card_wrapper(
            [
                dcc.Tabs(
                    id="pathnet-metrics-graphs",
                    value=ACC_TAB_NAME,
                    children=[
                        dcc.Tab(label="pathnet-metrics-positional", value=ACC_TAB_NAME),
                        dcc.Tab(label="pathnet-metrics-roles", value=ROLE_TAB_NAME),
                        dcc.Tab(label="DPs Quality", value=QUALITY_TAB_NAME),
                        dcc.Tab(label="Boundaries metrics", value=BOUNDARIES_TAB_NAME),
                    ],
                ),
            ]
        ),
        html.Div(id="pathnet-metrics-content"),
    ]
)


@callback(Output("pathnet-metrics-content", "children"), Input("pathnet-metrics-graphs", "value"))
def render_content(tab):
    return TABS_LAYOUTS[tab]
