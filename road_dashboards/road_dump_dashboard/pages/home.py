from dash import register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.logical_components import catalog_table

page_properties = PageProperties(
    order=0,
    icon="home",
    path="/home",
    title="RoadE2E Data Exploration Dashboard",
    extra_callable_layouts=[catalog_table.layout],
)
register_page(__name__, **page_properties.__dict__)


def layout():
    return page_properties.get_page_layout()
