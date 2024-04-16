from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dump_dashboard.components.logical_components.catalog_table import generate_catalog_layout

page_properties = PageProperties(icon="home", path="/home", name="Home")
register_page(__name__, order=0, **page_properties.__dict__)


def layout():
    home_page_layout = html.Div(
        [html.H1("RoadE2E Dump Dashboard", className="mb-5"), card_wrapper([generate_catalog_layout()])]
    )
    return home_page_layout
