from dash import dcc, html

from road_dump_dashboard.components.components_ids import (
    MD_TABLE,
    MD_COLUMNS_TO_TYPE,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_FILTERS,
    MD_COLUMNS_OPTION,
)


def init_dcc_stores():
    return html.Div(
        [
            dcc.Store(id=MD_TABLE),
            dcc.Store(id=MD_COLUMNS_TO_TYPE),
            dcc.Store(id=MD_COLUMNS_OPTION),
            dcc.Store(id=MD_COLUMNS_TO_DISTINCT_VALUES),
            dcc.Store(id=MD_FILTERS),
        ]
    )
