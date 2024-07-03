from dash import html, register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.logical_components import catalog_table

page_properties = PageProperties(
    order=0,
    icon="home",
    path="/home",
    title="RoadE2E Data Exploration Dashboard",
)
register_page(__name__, **page_properties.__dict__)


def layout():
    home_layout = html.Div(catalog_table.layout())
    return home_layout
