import base64
import json
import os
import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, DiskcacheManager, CeleryManager, Output, Input, State, callback, no_update
from uuid import uuid4

from road_dump_dashboard.components import sidebar, page_content
from road_dump_dashboard.components.dcc_stores import init_dcc_stores
from road_dump_dashboard.components.components_ids import (
    URL,
    DUMPS,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_TYPE,
)
from road_dump_dashboard.components.init_base_data import run_eval_db_manager, init_dumps, generate_meta_data_dicts

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


@callback(
    Output(DUMPS, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_TYPE, "data", allow_duplicate=True),
    Output(MD_COLUMNS_OPTION, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data", allow_duplicate=True),
    Input(URL, "hash"),
    State(DUMPS, "data"),
    background=True,
    prevent_initial_call=True,
)
def init_run(dumps_list, existing_dumps):
    if not dumps_list or existing_dumps:
        return no_update, no_update, no_update, no_update

    dumps_list = json.loads(base64.b64decode(dumps_list))
    rows = [run_eval_db_manager.get_item(dump_name) for dump_name in dumps_list]
    rows = pd.DataFrame(rows)
    dumps = init_dumps(rows)
    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = generate_meta_data_dicts(
        list(dumps["meta_data_tables"].values())[0]
    )

    return (
        dumps,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
    )


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6007", debug=True)
