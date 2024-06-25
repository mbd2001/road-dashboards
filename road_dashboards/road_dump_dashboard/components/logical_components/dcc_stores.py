from dash import dcc, html

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    CURR_DRAWN_GRAPH,
    IMAGES_IND,
    MD_FILTERS,
    TABLES,
)


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=TABLES),
            dcc.Store(id=MD_FILTERS),
            dcc.Store(id=IMAGES_IND),
            dcc.Store(id=CURR_DRAWN_GRAPH),
        ]
    )
