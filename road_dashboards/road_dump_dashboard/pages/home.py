from dash import register_page
from road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dump_dashboard.logical_components.grid_objects.catalog_table import CatalogTable
from road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator

page_properties = PageProperties(
    order=0,
    icon="home",
    path="/home",
    title="RoadE2E Data Exploration Dashboard",
)
register_page(__name__, **page_properties.__dict__)


layout = GridGenerator(CatalogTable()).layout()
