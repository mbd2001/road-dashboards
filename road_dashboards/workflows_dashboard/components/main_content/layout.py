import dash_bootstrap_components as dbc

from road_dashboards.workflows_dashboard.components.charts.charts_container import create_charts_container


def render_main_content() -> dbc.Col:
    return dbc.Col(
        [
            create_charts_container(),
        ],
        className="main-content overflow-auto h-100",
    )
