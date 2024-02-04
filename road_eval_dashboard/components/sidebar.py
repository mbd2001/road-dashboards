import dash_bootstrap_components as dbc
from dash import html, page_registry, callback, State, Output, Input

from road_eval_dashboard.components.components_ids import SIDEBAR, URL

MAFFE_LOGO = "https://gitlab.mobileye.com/uploads/-/system/project/avatar/807/index.jpeg"

def sidebar():
    return get_sidebar_layout()

@callback(
    Output(SIDEBAR, "children"),
    Input(URL, "hash"),
    background=True,
)
def update_sidebar(url):
    return get_sidebar_layout(url)

def get_sidebar_layout(url=""):
    layout = html.Div(
        [
            html.Div(
                [html.H2("Statistics")],
                className="sidebar-header",
            ),
            html.Hr(),
            dbc.Nav(
                [dbc.NavLink(
                    [
                        html.I(className=f"fas fa-book me-2"),
                        html.Span("Maffe Bins Docs", className="ms-2"),
                    ],
                    href="https://algoobjd-prod-1-backstage.sddc.mobileye.com/docs/your-group/component/maffe_bins",
                    active="exact",
                    target='_blank'
                )]
                +
                [
                    dbc.NavLink(
                        [
                            html.I(className=f"fas fa-{page['icon']} me-2"),
                            html.Span(page["name"], className="ms-2"),
                        ],
                        href=page["path"] + url,
                        active="exact",
                        external_link=True
                    )
                    for page in page_registry.values()
                    if not page["name"].startswith("Not")
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id=SIDEBAR,
        className="sidebar",
    )
    return layout