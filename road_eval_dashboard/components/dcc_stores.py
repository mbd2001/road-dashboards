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
    SCENE_SIGNALS_LIST,
)


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=NETS),
            dcc.Store(id=MD_COLUMNS_TO_TYPE),
            dcc.Store(id=MD_COLUMNS_OPTION),
            dcc.Store(id=MD_COLUMNS_TO_DISTINCT_VALUES),
            dcc.Store(id=MD_FILTERS),
            dcc.Store(id=PATHNET_FILTERS),
            dcc.Store(id=EFFECTIVE_SAMPLES_PER_BATCH),
            dcc.Store(id=NET_ID_TO_FB_BEST_THRESH),
            dcc.Store(id=SCENE_SIGNALS_LIST),
        ]
    )
