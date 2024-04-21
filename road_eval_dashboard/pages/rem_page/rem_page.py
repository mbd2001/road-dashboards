from dash import dcc, html, register_page

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.pages.rem_page.tabs import availability, accuracy, painted

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/rem", name="REM", order=9, **extra_properties.__dict__)

layout = html.Div(
    [
        html.H1("REM Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        dcc.Tabs([
        dcc.Tab(label='Accuracy', children=[accuracy.layout]),
        dcc.Tab(label='Availability', children=[availability.layout]),
        dcc.Tab(label='Painted', children=[painted.layout])
            ], style={"margin-top": 15})
    ]
)