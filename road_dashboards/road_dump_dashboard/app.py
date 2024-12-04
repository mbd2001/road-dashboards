import base64
import json
import os
import sys

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, Input, Output, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.logical_components.constants.components_ids import (
    LOAD_DATASETS_DATA_NOTIFICATION,
    URL,
)
from road_dashboards.road_dump_dashboard.logical_components.constants.init_data_sources import (
    EXISTING_TABLES,
    init_tables,
)
from road_dashboards.road_dump_dashboard.logical_components.grid_objects.catalog_table import dump_db_manager
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects import (
    load_datasets_modal,
    page_content,
    sidebar,
)
from road_dashboards.road_dump_dashboard.logical_components.multi_page_objects.dcc_stores import init_dcc_stores
from road_dashboards.road_dump_dashboard.table_schemes.custom_functions import dump_object

debug = False if os.environ.get("DEBUG") == "false" else True
if not debug:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
)


app.layout = html.Div(
    [
        init_dcc_stores(),
        dcc.Location(id=URL),
        sidebar.layout,
        load_datasets_modal.layout,
        page_content.layout,
    ]
)


@callback(Output(URL, "pathname"), Input(URL, "pathname"))
def redirect_to_home(pathname):
    if pathname == "/":
        return "/home"

    return no_update


@callback(
    [Output(table, "data") for table in EXISTING_TABLES],
    Output(LOAD_DATASETS_DATA_NOTIFICATION, "is_open"),
    Input(URL, "hash"),
)
def init_run(tables_list):
    if not tables_list:
        return *([no_update] * len(EXISTING_TABLES)), no_update

    datasets_ids = json.loads(base64.b64decode(tables_list))
    datasets = [dump_db_manager.get_item(datasets_id) for datasets_id in datasets_ids]
    datasets = pd.DataFrame(datasets)
    tables = get_tables(datasets)
    return *(dump_object(table) if table else None for table in tables), True


def get_tables(datasets):
    tables = init_tables(
        datasets["dump_name"],
        **{
            table: datasets[table].tolist()
            for table in datasets.columns
            if table.endswith("_table") and any(datasets[table])
        },
    )
    return tables


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6008", debug=debug, use_reloader=debug)
