from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

page_properties = PageProperties(icon="search", path="/batch_sampling", name="Batch Sampling")
register_page(__name__, order=4, **page_properties.__dict__)


layout = html.Div()
