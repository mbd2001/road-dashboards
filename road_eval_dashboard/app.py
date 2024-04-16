import os
from uuid import uuid4

import dash_bootstrap_components as dbc
from dash import CeleryManager, Dash, DiskcacheManager, Input, Output, State, dcc, html, no_update

from road_eval_dashboard.components import page_content, sidebar
from road_eval_dashboard.components.catalog_table import update_state_by_nets
from road_eval_dashboard.components.components_ids import (
    EFFECTIVE_SAMPLES_PER_BATCH,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NET_ID_TO_FB_BEST_THRESH,
    NETS,
    SCENE_SIGNALS_LIST,
    STATE_NOTIFICATION,
    URL,
)
from road_eval_dashboard.components.dcc_stores import init_dcc_stores
from road_eval_dashboard.components.meta_data_filter import recursive_build_meta_data_filters
from road_eval_dashboard.utils.url_state_utils import META_DATA_STATE_KEY, NETS_STATE_KEY, get_state

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
    routing_callback_inputs={
        # The app state is serialised in the URL hash without refreshing the page
        # This URL can be copied and then parsed on page load
        "state": State(URL, "hash"),
    },
)

app.layout = html.Div(
    [
        init_dcc_stores(),
        dcc.Location(id=URL),
        sidebar.sidebar(),
        page_content.layout,
    ],
    className="wrapper",
)


@app.callback(Output(URL, "pathname"), Input(URL, "pathname"))
def redirect_to_home(pathname):
    if pathname == "/":
        return "/home"

    return no_update


@app.callback(
    Output(NETS, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_TYPE, "data", allow_duplicate=True),
    Output(MD_COLUMNS_OPTION, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data", allow_duplicate=True),
    Output(EFFECTIVE_SAMPLES_PER_BATCH, "data", allow_duplicate=True),
    Output(NET_ID_TO_FB_BEST_THRESH, "data", allow_duplicate=True),
    Output(SCENE_SIGNALS_LIST, "data", allow_duplicate=True),
    Output(MD_FILTERS, "data", allow_duplicate=True),
    Output(STATE_NOTIFICATION, "children"),
    Input(URL, "hash"),
    State(NETS, "data"),
    State(MD_FILTERS, "data"),
    background=False,
    prevent_initial_call=True,
)
def init_run(state, nets, query):
    if not state or (nets and get_state(state, NETS_STATE_KEY) == nets):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    nets = get_state(state, NETS_STATE_KEY)

    (
        effective_samples_per_batch,
        md_columns_options,
        md_columns_to_distinguish_values,
        md_columns_to_type,
        net_id_to_best_thresh,
        scene_signals_list,
    ) = update_state_by_nets(nets)

    meta_data_filters_state = get_state(state, META_DATA_STATE_KEY)
    filters_str = (
        recursive_build_meta_data_filters(meta_data_filters_state[0]) if meta_data_filters_state else no_update
    )
    meta_data_filters_query = no_update if filters_str == query else filters_str

    notification = dbc.Alert("State loaded successfully!", color="success", dismissable=True, duration=2500, fade=True)
    return (
        nets,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        effective_samples_per_batch,
        net_id_to_best_thresh,
        scene_signals_list,
        meta_data_filters_query,
        notification,
    )


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6007", debug=True)
