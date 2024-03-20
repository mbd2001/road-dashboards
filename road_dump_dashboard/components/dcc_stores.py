from dash import dcc, html

from road_dump_dashboard.components.components_ids import TABLES, MD_FILTERS


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=TABLES),
            dcc.Store(id=MD_FILTERS),
        ]
    )
