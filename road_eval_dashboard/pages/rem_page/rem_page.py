from dash import dcc, html, register_page, callback, Output, Input

from road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_eval_dashboard.components.components_ids import REM_TABS_CONTENT, REM_TABS
from road_eval_dashboard.components.page_properties import PageProperties
from road_eval_dashboard.pages.rem_page.tabs import availability, accuracy, painted

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/rem", name="REM", order=9, **extra_properties.__dict__)

TABS_LAYOUTS = {'accuracy': accuracy.layout, "availability": availability.layout, "painted": painted.layout}

layout = html.Div(
    [
        html.H1("REM Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        dcc.Tabs(id=REM_TABS, value="accuracy", children=[
        dcc.Tab(label='Accuracy', value="accuracy"),
        dcc.Tab(label='Availability', value="availability"),
        dcc.Tab(label='Painted', value="painted")
            ], style={"margin-top": 15}),
        html.Div(id=REM_TABS_CONTENT)
    ]
)

@callback(
    Output(REM_TABS_CONTENT, 'children'),
    Input(REM_TABS, 'value')
)
def render_content(tab):
    return TABS_LAYOUTS[tab]