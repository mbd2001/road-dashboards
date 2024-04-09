from dash import dcc, html

from road_eval_dashboard.components.components_ids import (
    NETS,
    MD_COLUMNS_TO_TYPE,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_FILTERS,
    MD_COLUMNS_OPTION,
    PATHNET_FILTERS,
    EFFECTIVE_SAMPLES_PER_BATCH,
    NET_ID_TO_FB_BEST_THRESH,
    SCENE_SIGNALS_LIST, GRAPH_TO_COPY,
)


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=NETS, storage_type="session"),
            dcc.Store(id=GRAPH_TO_COPY, storage_type="session"),
            dcc.Store(id=MD_COLUMNS_TO_TYPE, storage_type="session"),
            dcc.Store(id=MD_COLUMNS_OPTION, storage_type="session"),
            dcc.Store(id=MD_COLUMNS_TO_DISTINCT_VALUES, storage_type="session"),
            dcc.Store(id=MD_FILTERS, storage_type="session"),
            dcc.Store(id=PATHNET_FILTERS, storage_type="session"),
            dcc.Store(id=EFFECTIVE_SAMPLES_PER_BATCH, storage_type="session"),
            dcc.Store(id=NET_ID_TO_FB_BEST_THRESH, storage_type="session"),
            dcc.Store(id=SCENE_SIGNALS_LIST, storage_type="session"),
        ]
    )
