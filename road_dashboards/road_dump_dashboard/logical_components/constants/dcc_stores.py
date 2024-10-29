from dash import dcc, html
from road_dump_dashboard.logical_components.constants.components_ids import CURR_DRAWN_GRAPH, IMAGES_IND
from road_dump_dashboard.logical_components.constants.init_data_sources import EXISTING_TABLES


def init_dcc_stores():
    return html.Div(
        [dcc.Store(id=table, data=None) for table in EXISTING_TABLES]
        + [
            dcc.Store(id=IMAGES_IND, data=0),
            dcc.Store(id=CURR_DRAWN_GRAPH),
        ]
    )
