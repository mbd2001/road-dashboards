from dash import register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties
from road_dashboards.road_dump_dashboard.components.graph_wrappers import countries_heatmap

page_properties = PageProperties(
    order=1,
    icon="search",
    path="/meta_data",
    title="Meta Data",
    objs_name="frames",
    main_table="meta_data",
    extra_callable_layouts=[countries_heatmap.layout],
)
register_page(__name__, **page_properties.__dict__)
layout = page_properties.get_page_layout()
