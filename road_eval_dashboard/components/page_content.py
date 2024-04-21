import dash_bootstrap_components as dbc
from dash import html, page_container

from road_eval_dashboard.components.components_ids import PAGE_CONTENT, STATE_NOTIFICATION
from road_eval_dashboard.components.layout_wrapper import loading_wrapper

layout = html.Div(
    [
        loading_wrapper(
            [
                html.Div(id=STATE_NOTIFICATION),
            ],
            True,
        ),
        page_container,
    ],
    id=PAGE_CONTENT,
    className="content",
)
