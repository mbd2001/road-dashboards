from dash import html, register_page

from road_eval_dashboard.road_dump_dashboard import PageProperties
from road_eval_dashboard.road_dump_dashboard.components.dashboard_layout import card_wrapper
from road_eval_dashboard.road_dump_dashboard.components.logical_components import catalog_table

page_properties = PageProperties(icon="home", path="/home", name="Home")
register_page(__name__, order=0, **page_properties.__dict__)


def layout():
    home_page_layout = html.Div(
        [html.H1("RoadE2E Dump Dashboard", className="mb-5"), card_wrapper(catalog_table.layout())]
    )
    return home_page_layout
