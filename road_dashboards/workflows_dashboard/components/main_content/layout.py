import dash_bootstrap_components as dbc

from road_dashboards.workflows_dashboard.components.charts.charts_container import ChartsContainer
from road_dashboards.workflows_dashboard.components.selectors.export.export_section import ExportSection


def render_main_content() -> dbc.Col:
    return dbc.Col(
        [
            ChartsContainer().render(),
            ExportSection().render(),
        ],
        className="main-content overflow-auto h-100",
    )
