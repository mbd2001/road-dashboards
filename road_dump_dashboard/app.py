import base64
import json
import os
import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, DiskcacheManager, CeleryManager, Output, Input, State, callback, no_update
from uuid import uuid4

from road_dump_dashboard.components.dashboard_layout import sidebar, page_content
from road_dump_dashboard.components.logical_components.dcc_stores import init_dcc_stores
from road_dump_dashboard.components.constants.components_ids import URL, TABLES
from road_dump_dashboard.components.logical_components.init_base_data import run_eval_db_manager, init_tables

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
    background=True,
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
