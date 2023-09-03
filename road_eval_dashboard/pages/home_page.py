from dash import html, register_page

from road_eval_dashboard.components.catalog_table import generate_catalog_layout
from road_eval_dashboard.components.layout_wrapper import card_wrapper
from road_eval_dashboard.components.page_properties import PageProperties


extra_properties = PageProperties("home")
register_page(__name__, path="/home", name="Home", order=0, **extra_properties.__dict__)


def layout():
    home_page_layout = html.Div(
        [html.H1("RoadE2E Metrics Dashboard", className="mb-5"), card_wrapper([generate_catalog_layout()])]
    )
    return home_page_layout
