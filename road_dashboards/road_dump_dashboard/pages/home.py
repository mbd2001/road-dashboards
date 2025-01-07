from dash import register_page

from road_dashboards.road_dump_dashboard.logical_components.constants.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import CatalogTable
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.grid_generator import GridGenerator

page = PageProperties(order=0, icon="home", path="/home", title="Data Exploration")
register_page(__name__, **page.__dict__)

catalog_table = CatalogTable()

layout = GridGenerator(catalog_table, warp_sub_objects=False).layout()
