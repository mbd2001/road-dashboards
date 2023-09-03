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
)
from road_eval_dashboard.components.layout_wrapper import loading_wrapper, card_wrapper
from road_eval_dashboard.components.page_properties import PageProperties


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
    ]
)
