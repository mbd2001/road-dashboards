import base64
import json
import os
from uuid import uuid4

import dash_bootstrap_components as dbc
import pandas as pd
from dash import CeleryManager, Dash, DiskcacheManager, Input, Output, State, callback, dcc, html, no_update

from road_dump_dashboard.components.constants.components_ids import TABLES, URL
from road_dump_dashboard.components.dashboard_layout import page_content, sidebar
from road_dump_dashboard.components.logical_components.catalog_table import init_tables, run_eval_db_manager
from road_dump_dashboard.components.logical_components.dcc_stores import init_dcc_stores

launch_uid = uuid4()
if "REDIS_URL" in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery

    celery_app = Celery(__name__, broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])
    background_callback_manager = CeleryManager(celery_app, cache_by=[lambda: launch_uid], expire=600)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache

    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache, cache_by=[lambda: launch_uid], expire=600)


app = Dash(
    __name__,
    background_callback_manager=background_callback_manager,
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

    tables_list = json.loads(base64.b64decode(tables_list))
    rows = [run_eval_db_manager.get_item(table) for table in tables_list]
    rows = pd.DataFrame(rows)
    tables = init_tables(rows)
    return tables


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6007", debug=True)
