from dash import html, register_page

from road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

extra_properties = PageProperties("search")
register_page(__name__, path="/batch_sampling", name="Batch Sampling", order=3, **extra_properties.__dict__)


layout = html.Div()
