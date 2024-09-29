from dash import dcc, html

from road_dashboards.road_eval_dashboard.components.components_ids import (
    BOUNDARY_DROP_DOWN,
    EFFECTIVE_SAMPLES_PER_BATCH,
    GRAPH_TO_COPY,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NET_ID_TO_FB_BEST_THRESH,
    NETS,
    PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD,
    PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES,
    PATHNET_EVENTS_BOOKMARKS_JSON,
    PATHNET_EVENTS_CHOSEN_NET,
    PATHNET_EVENTS_EXTRACTOR_DICT,
    PATHNET_EVENTS_REF_CHOSEN_NET,
    PATHNET_EXPLORER_DATA,
    PATHNET_FILTERS,
    SCENE_SIGNALS_LIST,
)


def init_events_extractor_dict():
    default_dict = {
        "net": None,
        "dp_source": None,
        "metric": None,
        "role": None,
        "dist": None,
        "threshold": None,
        "is_unique_on": None,
        "ref_net": None,
        "ref_dp_source": None,
        "ref_threshold": None,
        "num_events": None,
    }
    return default_dict


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
            dcc.Store(id=PATHNET_EVENTS_CHOSEN_NET, storage_type="session"),
            dcc.Store(id=PATHNET_EVENTS_REF_CHOSEN_NET, storage_type="session"),
            dcc.Store(id=PATHNET_EVENTS_BOOKMARKS_JSON, storage_type="session"),
            dcc.Store(id=PATHNET_EXPLORER_DATA, storage_type="session"),
            dcc.Store(id=PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, storage_type="session"),
            dcc.Store(id=PATHNET_DYNAMIC_THRESHOLD_BOUNDARIES, storage_type="session"),
            dcc.Store(id=BOUNDARY_DROP_DOWN, storage_type="session"),
            dcc.Store(id=PATHNET_EVENTS_EXTRACTOR_DICT, data=init_events_extractor_dict(), storage_type="session"),
        ]
    )
