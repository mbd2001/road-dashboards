import dash_bootstrap_components as dbc

from road_dashboards.workflows_dashboard.components.charts.charts_container import create_charts_container
from road_dashboards.workflows_dashboard.components.selectors.export.export_section import create_export_section


def render_main_content() -> dbc.Col:
    return dbc.Col(
        [
            create_charts_container(),
            create_export_section(),
        ],
        className="main-content overflow-auto h-100",
    )
