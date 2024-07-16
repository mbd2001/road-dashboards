import base64
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, Input, Output, State, callback, dcc, html, no_update

from road_dashboards.road_dump_dashboard.components.constants.components_ids import TABLES, URL
from road_dashboards.road_dump_dashboard.components.dashboard_layout import page_content, sidebar
from road_dashboards.road_dump_dashboard.components.logical_components.catalog_table import dump_db_manager, init_tables
from road_dashboards.road_dump_dashboard.components.logical_components.dcc_stores import init_dcc_stores

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
        sidebar.sidebar(),
        page_content.layout,
    ]
)


@app.callback(Output(URL, "pathname"), Input(URL, "pathname"))
def redirect_to_home(pathname):
    if pathname == "/":
        return "/home"

    return no_update


@callback(
    Output(TABLES, "data", allow_duplicate=True),
    Input(URL, "hash"),
    State(TABLES, "data"),
    prevent_initial_call=True,
)
def init_run(tables_list, existing_tables):
    if not tables_list or existing_tables:
        return no_update

    datasets_ids = json.loads(base64.b64decode(tables_list))
    datasets = [dump_db_manager.get_item(datasets_id) for datasets_id in datasets_ids]
    datasets = pd.DataFrame(datasets)
    tables = init_tables(datasets)
    return tables


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6013", debug=True)
