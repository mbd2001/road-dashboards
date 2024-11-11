import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html, page_registry

from road_dashboards.road_eval_dashboard.components.components_ids import SIDEBAR, URL

MAFFE_LOGO = "https://gitlab.mobileye.com/uploads/-/system/project/avatar/807/index.jpeg"


def sidebar():
    return html.Div(
        id=SIDEBAR,
        className="sidebar",
    )


@callback(
    Output(SIDEBAR, "children"),
    Input(URL, "hash"),
)
def update_sidebar(url):
    layout = [
        html.Div(
            [html.H2("Statistics")],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.I(className="fas fa-book me-2"),
                        html.Span("Maffe Bins Docs", className="ms-2"),
                    ],
                    href="https://algoobjd-prod-1-backstage.sddc.mobileye.com/docs/your-group/component/maffe_bins",
                    active="exact",
                    target="_blank",
                    external_link=True,
                )
            ]
            + [
                dbc.NavLink(
                    [
                        html.I(className=f"fas fa-{page['icon']} me-2"),
                        html.Span(page["name"], className="ms-2"),
                    ],
                    href=page["path"] + url,
                    active="exact",
                )
                for page in page_registry.values()
                if not page["name"].startswith("Not")
            ],
            vertical=True,
            pills=True,
        ),
    ]
    return layout
