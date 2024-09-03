from dash import dcc, html

from road_dashboards.road_dump_dashboard.components.constants.components_ids import (
    CURR_DRAWN_GRAPH,
    IMAGES_IND,
    MAIN_TABLES,
    MD_TABLES,
    PAGE_FILTERS,
)
from road_dashboards.road_dump_dashboard.components.logical_components.tables_properties import POTENTIAL_TABLES


def init_dcc_stores():
    return html.Div(
        [dcc.Store(id=table) for table in POTENTIAL_TABLES]
        + [
            dcc.Store(id=MAIN_TABLES),
            dcc.Store(id=MD_TABLES),
            dcc.Store(id=PAGE_FILTERS),
            dcc.Store(id=IMAGES_IND),
            dcc.Store(id=CURR_DRAWN_GRAPH),
        ]
    )
