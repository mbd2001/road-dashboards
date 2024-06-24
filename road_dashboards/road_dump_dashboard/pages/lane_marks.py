from dash import register_page

from road_dashboards.road_dump_dashboard.components.common_pages_layout.page_properties import PageProperties

page_properties = PageProperties(
    order=2,
    icon="search",
    path="/lane_marks",
    title="Lane Marks",
    objs_name="lane marks",
    main_table="lm_meta_data",
    meta_data_table="meta_data",
)
register_page(__name__, **page_properties.__dict__)
layout = page_properties.get_page_layout()
