from dash import dcc, html

from road_dump_dashboard.components.constants.components_ids import MD_FILTERS, TABLES


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=TABLES),
            dcc.Store(id=MD_FILTERS),
        ]
    )
