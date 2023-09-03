import dash_bootstrap_components as dbc
from dash import html, page_registry

from road_eval_dashboard.components.components_ids import SIDEBAR

MAFFE_LOGO = "https://gitlab.mobileye.com/uploads/-/system/project/avatar/807/index.jpeg"


def sidebar():
    layout = html.Div(
        [
            html.Div(
                [
                    html.A(
                        href="https://algoobjd-prod-1-backstage.sddc.mobileye.com/docs/your-group/component/maffe_bins",
                        children=[
                            html.Img(
                                alt="maffe_bins documentation",
                                src=MAFFE_LOGO,
                                style={"width": "3rem"},
                            )
                        ],
                    ),
                    html.H2("Statistics"),
                ],
                className="sidebar-header",
            ),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className=f"fas fa-{page['icon']} me-2"),
                            html.Span(page["name"], className="ms-2"),
                        ],
                        href=page["path"],
                        active="exact",
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
