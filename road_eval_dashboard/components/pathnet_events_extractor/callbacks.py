import copy
import json
import time

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, no_update

from road_eval_dashboard.components.components_ids import (
    MD_FILTERS,
    NETS,
    PATHNET_BOOKMARKS_JSON_FILE_NAME,
    PATHNET_EVENTS_BOOKMARKS_JSON,
    PATHNET_EVENTS_CHOSEN_NET,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_ERROR_MESSAGE,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_ORDER_DROPDOWN,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EXPLORER_DATA,
    PATHNET_EXPORT_JSON_BUTTON,
    PATHNET_EXPORT_JSON_LOG_MESSAGE,
    PATHNET_EXPORT_TO_BOOKMARK_WINDOW,
    PATHNET_GT,
    PATHNET_OPEN_EXPORT_EVENTS_WINDOW_BUTTON,
    PATHNET_PRED,
)
from road_eval_dashboard.components.queries_manager import (
    generate_avail_query,
    generate_pathnet_events_query,
    run_query_with_nets_names_processing,
)
from road_eval_dashboard.utils.url_state_utils import create_dropdown_options_list, create_message

BOOKMARKS_COLUMNS = ["batch_num", "sample_index"]
MF_EXPLORER_PARAMS = """ 
    --dataset_names {dataset} 
    --population population=test 
    --net_name {net_id} 
    --ckpt {checkpoint} 
    --prediction_mode mf
"""


@callback(
    Output(PATHNET_EVENTS_NET_ID_DROPDOWN, "options"),
    Input(NETS, "data"),
)
def get_eval_name(nets):
    return create_dropdown_options_list(nets["names"]) if nets else no_update


@callback(
    Output(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "options"),
    Input(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(MD_FILTERS, "data"),
    prevent_initial_call=True,
)
def create_dp_source_dropdown(net, meta_data_filters):
    if not net:
        return no_update

    query = generate_avail_query(
        net[PATHNET_PRED],
        net["meta_data"],
        meta_data_filters,
        column_name="bin_population",
    )
    df, _ = run_query_with_nets_names_processing(query)
    return create_dropdown_options_list(labels=df["bin_population"])


@callback(
    Output(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(NETS, "data"),
    Input(PATHNET_EVENTS_NET_ID_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_chosen_net_data(nets, chosen_net_id):
    if not nets or not chosen_net_id:
        return no_update

    net = copy.deepcopy(nets)
    net_id_ind = [i for i, net_id in enumerate(nets["names"]) if net_id == chosen_net_id][0]
    net["names"] = net["names"][net_id_ind : net_id_ind + 1]
    net["frame_tables"]["paths"] = net["frame_tables"]["paths"][net_id_ind : net_id_ind + 1]
    net[PATHNET_PRED]["paths"] = net[PATHNET_PRED]["paths"][net_id_ind : net_id_ind + 1]
    net[PATHNET_GT]["paths"] = net[PATHNET_GT]["paths"][net_id_ind : net_id_ind + 1]
    return net


def check_build_events_input(n_clicks, mandatory_args):
    if not n_clicks:
        return False, ""

    if not all(mandatory_args):
        return False, "Please specify an option for each dropdown."

    return True, ""


def check_events_df_sanity(events_df):
    if events_df.empty:
        return False, "Events DataFrame is empty"

    for column in BOOKMARKS_COLUMNS:
        if column not in events_df.columns:
            return False, f"Events DataFrame is missing '{column}' column"

    return True, ""


def converts_events_df_to_bookmarks_json(events_df):
    comment_columns = [col for col in events_df.columns if col not in BOOKMARKS_COLUMNS]

    df_as_bookmarks = pd.DataFrame()

    for bookmark_col in BOOKMARKS_COLUMNS:
        df_as_bookmarks[bookmark_col] = events_df[bookmark_col].astype(int)

    df_as_bookmarks["comment"] = events_df[comment_columns].apply(
        lambda row: "; ".join(f"{col}={val}" for col, val in row.items()), axis=1
    )

    return df_as_bookmarks.to_json(date_format="iso", orient="split")


def create_data_dict_for_explorer(net_name, dp_source, role, dist, metric):
    net_id, checkpoint, _, dataset = net_name.split("__")
    bookmarks_name = f"{net_id}_{dp_source}_{role}_{dist}_{metric}"
    explorer_params = MF_EXPLORER_PARAMS.format(dataset=dataset, net_id=net_id, checkpoint=checkpoint)

    return {"bookmarks_name": bookmarks_name, "explorer_params": explorer_params}


@callback(
    Output(PATHNET_EVENTS_DATA_TABLE, "data"),
    Output(PATHNET_EVENTS_DATA_TABLE, "columns"),
    Output(PATHNET_EVENTS_BOOKMARKS_JSON, "data"),
    Output(PATHNET_EXPLORER_DATA, "data"),
    Output(PATHNET_EVENTS_ERROR_MESSAGE, "children"),
    State(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "value"),
    Input(PATHNET_EVENTS_SUBMIT_BUTTON, "n_clicks"),
    State(MD_FILTERS, "data"),
    State(PATHNET_EVENTS_ROLE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_DIST_DROPDOWN, "value"),
    State(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    State(PATHNET_EVENTS_ORDER_DROPDOWN, "value"),
    State(PATHNET_EVENTS_NUM_EVENTS, "value"),
    prevent_initial_call=True,
)
def build_events_df(net, dp_source, n_clicks, meta_data_filters, role, dist, metric, order, samples_num):
    DEFAULT_SAMPLES_NUM = 200

    dropdown_args = (net, dp_source, role, dist, metric, order)
    input_valid, input_error_message = check_build_events_input(n_clicks, dropdown_args)
    if not input_valid:
        return no_update, no_update, no_update, no_update, create_message(input_error_message)

    if metric == "false":
        role = [f"'{role}'", f"'unmatched-{role}'"]

    query = generate_pathnet_events_query(
        data_tables=net[PATHNET_PRED],
        meta_data=net["meta_data"],
        meta_data_filters=meta_data_filters,
        dp_source=dp_source,
        role=role,
        dist=float(dist),
        metric=metric,
        order=order,
    )
    df, _ = run_query_with_nets_names_processing(query)
    df = df.head(samples_num if samples_num else DEFAULT_SAMPLES_NUM)

    df_sane, sanity_error_message = check_events_df_sanity(events_df=df)
    if not df_sane:
        return no_update, no_update, no_update, no_update, create_message(sanity_error_message)

    bookmarks_json = converts_events_df_to_bookmarks_json(events_df=df)
    data_for_explorer = create_data_dict_for_explorer(net["names"][0], dp_source, role, dist, metric)

    data_table = df.to_dict("records")
    final_cols = [{"name": col, "id": col, "deletable": False, "selectable": True} for col in df.columns]

    return data_table, final_cols, bookmarks_json, data_for_explorer, create_message(msg="Extracted!", color="green")


@callback(
    Output(PATHNET_EXPORT_TO_BOOKMARK_WINDOW, "is_open", allow_duplicate=True),
    Input(PATHNET_OPEN_EXPORT_EVENTS_WINDOW_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_export_to_bookmark_window_opening(n_clicks):
    return n_clicks > 0


@callback(
    Output(PATHNET_EXPORT_JSON_BUTTON, "disabled", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "className", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "children", allow_duplicate=True),
    Input(PATHNET_EXPORT_JSON_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def on_pathnet_export_json_button_clicked(n_clicks):
    return True, "me-1", dbc.Spinner(size="sm")


@callback(
    Output(PATHNET_EXPORT_JSON_BUTTON, "className", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "color", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "children", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_LOG_MESSAGE, "children", allow_duplicate=True),
    Input(PATHNET_EXPORT_JSON_BUTTON, "disabled"),
    State(PATHNET_BOOKMARKS_JSON_FILE_NAME, "value"),
    State(PATHNET_EVENTS_BOOKMARKS_JSON, "data"),
    State(PATHNET_EXPLORER_DATA, "data"),
    prevent_initial_call=True,
)
def dump_bookmarks_json(disabled, file_path, serialized_json, explorer_data):
    if not all([disabled, file_path, serialized_json]):
        return no_update, no_update, no_update, no_update

    bookmarks_file_name = explorer_data["bookmarks_name"]
    explore_params = explorer_data["explorer_params"]
    json_path = f"{file_path}/{bookmarks_file_name}.json"
    try:
        bookmarks_final_format = json.loads(serialized_json)["data"]
        with open(json_path, "w") as f:
            json.dump(bookmarks_final_format, f, indent=4)

        success_message = f"Bookmarks dumped to: '{json_path}'.\n Params for explorer: {explore_params}"
        return "", "success", "Exported!", create_message(success_message, color="green")

    except (json.JSONDecodeError, TypeError) as e:
        error_message = f"Invalid to decode json format.\nTraceback: {e}"
    except IOError as e:
        error_message = f"Dumping json to:\n '{json_path}' failed.\nTraceback: {e}"

    return "", "red", "Failed!", create_message(error_message)


@callback(
    Output(PATHNET_EXPORT_TO_BOOKMARK_WINDOW, "is_open", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "color", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "children", allow_duplicate=True),
    Output(PATHNET_EXPORT_JSON_BUTTON, "disabled", allow_duplicate=True),
    Input(PATHNET_EXPORT_JSON_BUTTON, "children"),
    prevent_initial_call=True,
)
def on_dump_bookmarks_json_process_finished(children):
    if children not in ["Failed!", "Exported!"]:  # haven't changed / in loading state
        return no_update, no_update, no_update, no_update
    time.sleep(30)
    return children == "Failed!", "primary", "Export", False
