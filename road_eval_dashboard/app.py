import os
from queue import Queue
from threading import Thread
from uuid import uuid4

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, DiskcacheManager, CeleryManager, Output, Input, State, no_update

from road_eval_dashboard.components import sidebar, page_content
from road_eval_dashboard.components.catalog_table import wrapper
from road_eval_dashboard.components.components_ids import URL, NETS, MD_COLUMNS_TO_TYPE, MD_COLUMNS_OPTION, \
    MD_COLUMNS_TO_DISTINCT_VALUES, EFFECTIVE_SAMPLES_PER_BATCH, NET_ID_TO_FB_BEST_THRESH, SCENE_SIGNALS_LIST, \
    STATE_NOTIFICATION
from road_eval_dashboard.components.dcc_stores import init_dcc_stores
from road_eval_dashboard.components.init_threads import (
    generate_meta_data_dicts,
    generate_effective_samples_per_batch,
    get_best_fb_per_net,
    get_list_of_scene_signals,
)
from road_eval_dashboard.components.net_properties import Nets

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
    ], className="wrapper"
)

@app.callback(Output(URL, "pathname"), Input(URL, "pathname"))
def redirect_to_home(pathname):
    if pathname == "/":
        return "/home"


@app.callback(
    Output(NETS, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_TYPE, "data", allow_duplicate=True),
    Output(MD_COLUMNS_OPTION, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data", allow_duplicate=True),
    Output(EFFECTIVE_SAMPLES_PER_BATCH, "data", allow_duplicate=True),
    Output(NET_ID_TO_FB_BEST_THRESH, "data", allow_duplicate=True),
    Output(SCENE_SIGNALS_LIST, "data", allow_duplicate=True),
    Output(STATE_NOTIFICATION, "children"),
    Input(URL, "hash"),
    State(NETS, "data"),
    background=False,
    prevent_initial_call=True,
)
def init_run(state, nets):
    if not state or (nets and Nets.nets_dict_to_hash(nets) == state):
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    nets = Nets.hash_to_nets_dict(state)

    q1, q2, q3, q4 = Queue(), Queue(), Queue(), Queue()
    Thread(target=wrapper, args=(generate_meta_data_dicts, nets, q1)).start()
    Thread(target=wrapper, args=(generate_effective_samples_per_batch, nets, q2)).start()
    Thread(target=wrapper, args=(get_best_fb_per_net, nets, q3)).start()
    Thread(target=wrapper, args=(get_list_of_scene_signals, nets, q4)).start()

    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = q1.get()
    effective_samples_per_batch = q2.get()
    net_id_to_best_thresh = q3.get()
    scene_signals_list = q4.get()

    notification = dbc.Alert("State loaded successfully!", color="success", dismissable=True)
    return (
        nets,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        effective_samples_per_batch,
        net_id_to_best_thresh,
        scene_signals_list,
        notification
    )

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="6003", debug=True)
