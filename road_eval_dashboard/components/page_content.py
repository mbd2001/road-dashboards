from dash import html, page_container

from road_eval_dashboard.components.components_ids import PAGE_CONTENT

layout = html.Div(page_container, id=PAGE_CONTENT, className="content")
