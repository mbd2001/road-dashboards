from dash import register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

page_properties = PageProperties(
    order=3,
    icon="search",
    path="/pathnet",
    title="Pathnet",
    objs_name="DPs",
    main_table="rpw_meta_data",
    meta_data_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)
layout = page_properties.get_page_layout()
