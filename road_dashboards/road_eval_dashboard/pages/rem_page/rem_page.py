from dash import Input, Output, callback, dcc, html, register_page

from road_dashboards.road_eval_dashboard.components import base_dataset_statistics, meta_data_filter
from road_dashboards.road_eval_dashboard.components.components_ids import REM_ROLES_DROPDOWN, REM_TABS, REM_TABS_CONTENT
from road_dashboards.road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_dashboards.road_eval_dashboard.components.page_properties import PageProperties
from road_dashboards.road_eval_dashboard.components.queries_manager import Roles
from road_dashboards.road_eval_dashboard.pages.rem_page.tabs import accuracy, availability, painted

extra_properties = PageProperties("line-chart")
register_page(__name__, path="/rem", name="REM", order=9, **extra_properties.__dict__)

TABS_LAYOUTS = {"accuracy": accuracy.layout, "availability": availability.layout, "painted": painted.layout}


def get_settings_layout():
    roles_options = {s.value: s.name.capitalize() for s in Roles}
    return card_wrapper(
        [
            html.H6("Choose Role"),
            dcc.Dropdown(roles_options, Roles.HOST, id=REM_ROLES_DROPDOWN),
        ]
    )


layout = html.Div(
    [
        html.H1("REM Metrics", className="mb-5"),
        meta_data_filter.layout,
        base_dataset_statistics.frame_layout,
        get_settings_layout(),
        dcc.Tabs(
            id=REM_TABS,
            value="accuracy",
            children=[
                dcc.Tab(label="Accuracy", value="accuracy"),
                dcc.Tab(label="Availability", value="availability"),
                dcc.Tab(label="Painted", value="painted"),
            ],
            style={"margin-top": 15},
        ),
        html.Div(id=REM_TABS_CONTENT),
    ]
)


@callback(Output(REM_TABS_CONTENT, "children"), Input(REM_TABS, "value"))
def render_content(tab):
    return TABS_LAYOUTS[tab]
