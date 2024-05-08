from queue import Queue
from threading import Thread

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, callback, ctx, dash_table, html, no_update
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_eval_dashboard.components.components_ids import (
    CATALOG,
    EFFECTIVE_SAMPLES_PER_BATCH,
    LOAD_NETS_DATA_NOTIFICATION,
    MD_COLUMNS_OPTION,
    MD_COLUMNS_TO_DISTINCT_VALUES,
    MD_COLUMNS_TO_TYPE,
    NET_ID_TO_FB_BEST_THRESH,
    NETS,
    RUN_EVAL_CATALOG,
    SCENE_SIGNALS_LIST,
    UPDATE_RUNS_BTN,
    URL,
)
from road_eval_dashboard.components.init_threads import (
    generate_effective_samples_per_batch,
    generate_meta_data_dicts,
    get_best_fb_per_net,
    get_list_of_scene_signals,
)
from road_eval_dashboard.components.layout_wrapper import loading_wrapper
from road_eval_dashboard.components.net_properties import Nets
from road_eval_dashboard.utils.url_state_utils import NETS_STATE_KEY, add_state

run_eval_db_manager = DBManager(table_name="algoroad_run_eval")


def generate_catalog_layout():
    layout = html.Div(
        [
            dbc.Row(html.H2("Net Catalog", className="mb-5")),
            dbc.Row(
                dash_table.DataTable(
                    id=RUN_EVAL_CATALOG,
                    columns=[
                        {"name": i, "id": i, "deletable": False, "selectable": True}
                        for i in [
                            "net",
                            "checkpoint",
                            "dataset",
                            "population",
                            "use_case",
                            "total_frames",
                            "user",
                            "last_change",
                        ]
                    ],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    sort_by=[
                        {"column_id": "last_change", "direction": "desc"},
                    ],
                    row_selectable="multi",
                    selected_rows=[],
                    page_action="native",
                    page_current=0,
                    page_size=20,
                    css=[{"selector": ".show-hide", "rule": "display: none"}],
                    style_cell={"textAlign": "left"},
                    style_header={
                        "background-color": "#4e4e50",
                        "fontWeight": "bold",
                        "color": "white",
                    },
                    style_data={
                        "backgroundColor": "white",
                        "color": "rgb(102, 102, 102)",
                    },
                    style_table={
                        "border": "1px solid rgb(230, 230, 230)",
                    },
                )
            ),
            dbc.Row(
                dbc.Col(dbc.Button("Choose Runs to Compare", id=UPDATE_RUNS_BTN, className="bg-primary mt-5")),
            ),
            loading_wrapper([html.Div(id=LOAD_NETS_DATA_NOTIFICATION)]),
        ]
    )
    return layout


@callback(
    Output(NETS, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_TYPE, "data", allow_duplicate=True),
    Output(MD_COLUMNS_OPTION, "data", allow_duplicate=True),
    Output(MD_COLUMNS_TO_DISTINCT_VALUES, "data", allow_duplicate=True),
    Output(EFFECTIVE_SAMPLES_PER_BATCH, "data", allow_duplicate=True),
    Output(NET_ID_TO_FB_BEST_THRESH, "data", allow_duplicate=True),
    Output(SCENE_SIGNALS_LIST, "data", allow_duplicate=True),
    Output(LOAD_NETS_DATA_NOTIFICATION, "children", allow_duplicate=True),
    Output(URL, "hash", allow_duplicate=True),
    Input(UPDATE_RUNS_BTN, "n_clicks"),
    State(CATALOG, "data"),
    State(RUN_EVAL_CATALOG, "selected_rows"),
    prevent_initial_call=True,
)
def init_run(n_clicks, rows, derived_virtual_selected_rows):
    if not n_clicks or not derived_virtual_selected_rows:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    nets = init_nets(rows, derived_virtual_selected_rows)
    new_state = add_state(NETS_STATE_KEY, nets)
    (
        effective_samples_per_batch,
        md_columns_options,
        md_columns_to_distinguish_values,
        md_columns_to_type,
        net_id_to_best_thresh,
        scene_signals_list,
    ) = update_state_by_nets(nets)

    notification = dbc.Alert("Nets data loaded successfully!", color="success", dismissable=True)
    return (
        nets,
        md_columns_to_type,
        md_columns_options,
        md_columns_to_distinguish_values,
        effective_samples_per_batch,
        net_id_to_best_thresh,
        scene_signals_list,
        notification,
        new_state,
    )


def update_state_by_nets(nets):
    q1, q2, q3, q4 = Queue(), Queue(), Queue(), Queue()
    Thread(target=wrapper, args=(generate_meta_data_dicts, nets, q1)).start()
    Thread(target=wrapper, args=(generate_effective_samples_per_batch, nets, q2)).start()
    Thread(target=wrapper, args=(get_best_fb_per_net, nets, q3)).start()
    Thread(target=wrapper, args=(get_list_of_scene_signals, nets, q4)).start()
    md_columns_to_type, md_columns_options, md_columns_to_distinguish_values = q1.get()
    effective_samples_per_batch = q2.get()
    net_id_to_best_thresh = q3.get()
    scene_signals_list = q4.get()
    return (
        effective_samples_per_batch,
        md_columns_options,
        md_columns_to_distinguish_values,
        md_columns_to_type,
        net_id_to_best_thresh,
        scene_signals_list,
    )


def wrapper(func, arg, queue):
    queue.put(func(arg))


def init_nets(rows, derived_virtual_selected_rows):
    rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
    nets = Nets(
        rows["net"],
        rows["checkpoint"],
        rows["use_case"],
        rows["population"],
        rows["dataset"],
        **{table: rows[table].tolist() for table in rows.columns if table.endswith("_table") and any(rows[table])},
    ).__dict__
    return nets
