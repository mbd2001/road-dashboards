from dash import html, page_container

from road_eval_dashboard.components.components_ids import PAGE_CONTENT, STATE_NOTIFICATION
from road_eval_dashboard.components.layout_wrapper import loading_wrapper
import dash_bootstrap_components as dbc

layout = html.Div(
    [loading_wrapper([dbc.Alert("copied!", id="saved_alert", color="success", is_open=False, duration=4000, fade=True), html.Div(id=STATE_NOTIFICATION)], True), page_container], id=PAGE_CONTENT, className="content"
)
