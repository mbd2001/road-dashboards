import dash_bootstrap_components as dbc

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import (
    LOAD_DATASETS_DATA_NOTIFICATION,
)

layout = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Success"), close_button=False),
        dbc.ModalBody("Datasets loaded successfully"),
    ],
    id=LOAD_DATASETS_DATA_NOTIFICATION,
    is_open=False,
)
