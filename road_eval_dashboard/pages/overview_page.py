import dash_bootstrap_components as dbc
from dash import html, dcc, register_page

from road_eval_dashboard.components import (
    meta_data_filter,
    base_dataset_statistics,
    fb_meta_data_filters,
)
from road_eval_dashboard.components.components_ids import (
    COLOR_OVERALL,
    TYPE_OVERALL,
    LM_3D_ACC_HOST,
    LM_3D_ACC_NEXT,
    LM_3D_ACC_HOST_Z_X,
)
from road_eval_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.pages.card_generators import view_range_histogram_card, get_host_next_graph

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/overview", name="Overview", order=2, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("Overview", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.gt_layout,
        fb_meta_data_filters.layout,
        card_wrapper(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=COLOR_OVERALL, config={"displayModeBar": False})])], width=6
                        ),
                        dbc.Col(
                            [loading_wrapper([dcc.Graph(id=TYPE_OVERALL, config={"displayModeBar": False})])], width=6
                        ),
                    ]
                ),
            ]
        ),
        get_host_next_graph(
            {"type": LM_3D_ACC_HOST, "extra_filter": ""},
            {"type": LM_3D_ACC_NEXT, "extra_filter": ""},
            {"type": LM_3D_ACC_HOST_Z_X, "extra_filter": ""},
        ),
        view_range_histogram_card(),
    ]
)
