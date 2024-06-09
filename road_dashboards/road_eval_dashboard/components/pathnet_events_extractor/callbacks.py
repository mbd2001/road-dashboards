import copy
import json

import pandas as pd
from botocore.exceptions import ClientError
from dash import Input, Output, State, callback, no_update
from road_database_toolkit.cloud_file_system.file_operations import path_join, write_json

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NETS,
    PATHNET_EVENTS_BOOKMARKS_JSON,
    PATHNET_EVENTS_CHOSEN_NET,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_ORDER_DROPDOWN,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EXPLORER_DATA,
    PATHNET_EXPORT_TO_BOOKMARK_BUTTON,
    PATHNET_EXTRACT_EVENTS_LOG_MESSAGE,
    PATHNET_GT,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_avail_query,
    generate_pathnet_events_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_alert_message, create_dropdown_options_list

BOOKMARKS_COLUMNS = ["batch_num", "sample_index"]
EXPLORER_PARAMS = """ 
    --dataset_names {dataset} 
    --population {population} 
    --net_name {net_id} 
    --ckpt {checkpoint} 
    --use_case {use_case} 
    --bookmarks {bookmarks_name}
"""
S3_EVENTS_DIR = (
    "s3://mobileye-team-road/roade2e_database/run_eval_catalog/{net_id}/{checkpoint}/{use_case}/{dataset}/events"
)


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
    net["nets_info"] = net["nets_info"][net_id_ind]
    return net


def check_build_events_input(n_clicks, meta_data_columns, mandatory_args):
    if not n_clicks:
        return False, ""

    if not all(mandatory_column in meta_data_columns for mandatory_column in ["sample_index", "batch_num"]):
        return False, "This eval's meta-data is missing of (sample_index, batch_num) columns"

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

    return df_as_bookmarks.to_dict(orient="split")["data"]


def create_data_dict_for_explorer(net_info, dp_source, role, dist, metric):
    s3_dir_path = S3_EVENTS_DIR.format(
        dataset=net_info["dataset"],
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
    )
    bookmarks_file_name = f"{metric}_{dp_source}_{role}_dist{dist}"
    explorer_params = EXPLORER_PARAMS.format(
        dataset=net_info["dataset"],
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
        population=net_info["population"],
        bookmarks_name=bookmarks_file_name,
    )
    if dp_source == "mf":
        explorer_params += " --mf_predictions"
    return {"s3_dir_path": s3_dir_path, "bookmarks_name": bookmarks_file_name, "explorer_params": explorer_params}


def get_events_df(dist, dp_source, meta_data_cols, meta_data_filters, metric, net, order, role, samples_num):
    DEFAULT_SAMPLES_NUM = 200
    query = generate_pathnet_events_query(
        data_tables=net[PATHNET_PRED],
        meta_data=net["meta_data"],
        meta_data_filters=meta_data_filters,
        meta_data_columns=meta_data_cols,
        dp_source=dp_source,
        role=([f"'{role}'", f"'unmatched-{role}'"] if metric == "false" else role),
        dist=float(dist),
        metric=metric,
        order=order,
    )
    df, _ = run_query_with_nets_names_processing(query)
    df = df.head(samples_num if samples_num else DEFAULT_SAMPLES_NUM)
    return df


@callback(
    Output(PATHNET_EVENTS_DATA_TABLE, "data"),
    Output(PATHNET_EVENTS_DATA_TABLE, "columns"),
    Output(PATHNET_EVENTS_BOOKMARKS_JSON, "data"),
    Output(PATHNET_EXPLORER_DATA, "data"),
    Output(PATHNET_EXTRACT_EVENTS_LOG_MESSAGE, "children"),
    State(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "value"),
    Input(PATHNET_EVENTS_SUBMIT_BUTTON, "n_clicks"),
    State(MD_FILTERS, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
    State(PATHNET_EVENTS_ROLE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_DIST_DROPDOWN, "value"),
    State(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    State(PATHNET_EVENTS_ORDER_DROPDOWN, "value"),
    State(PATHNET_EVENTS_NUM_EVENTS, "value"),
    prevent_initial_call=True,
)
def build_events_df(
    net, dp_source, n_clicks, meta_data_filters, meta_data_cols, role, dist, metric, order, samples_num
):
    dropdown_args = (net, dp_source, role, dist, metric, order)
    input_valid, input_error_message = check_build_events_input(n_clicks, meta_data_cols, dropdown_args)
    if not input_valid:
        return no_update, no_update, no_update, no_update, create_alert_message(input_error_message, color="warning")

    df = get_events_df(dist, dp_source, meta_data_cols, meta_data_filters, metric, net, order, role, samples_num)
    df_sane, sanity_error_message = check_events_df_sanity(events_df=df)
    if not df_sane:
        return no_update, no_update, no_update, no_update, create_alert_message(sanity_error_message, color="warning")

    bookmarks_json = converts_events_df_to_bookmarks_json(events_df=df)
    data_for_explorer = create_data_dict_for_explorer(net["nets_info"], dp_source, role, dist, metric)

    data_table = df.to_dict("records")
    final_cols = [{"name": col, "id": col, "deletable": False, "selectable": True} for col in df.columns]

    return (
        data_table,
        final_cols,
        bookmarks_json,
        data_for_explorer,
        create_alert_message(msg="Extracted events successfully!", color="success"),
    )


@callback(
    Output(PATHNET_EXTRACT_EVENTS_LOG_MESSAGE, "children", allow_duplicate=True),
    Input(PATHNET_EXPORT_TO_BOOKMARK_BUTTON, "n_clicks"),
    State(PATHNET_EVENTS_BOOKMARKS_JSON, "data"),
    State(PATHNET_EXPLORER_DATA, "data"),
    prevent_initial_call=True,
)
def dump_bookmarks_json(n_clicks, bookmarks_dict, explorer_data):
    if not all([n_clicks, bookmarks_dict, explorer_data]):
        return no_update

    s3_dir_path = explorer_data["s3_dir_path"]
    bookmarks_file_name = explorer_data["bookmarks_name"]
    explore_params = explorer_data["explorer_params"]

    s3_full_path = path_join(s3_dir_path, f"{bookmarks_file_name}.json")
    try:
        write_json(s3_full_path, bookmarks_dict)
        success_message = f"Bookmarks dumped to:\n{s3_full_path}\n\nParams for explorer: {explore_params}"
        return create_alert_message(success_message, color="success")

    except (json.JSONDecodeError, TypeError) as e:
        error_message = f"Invalid to decode json format.\nTraceback: {e}"
    except ClientError as e:
        error_message = f"Error uploading to S3:\n'{s3_full_path}' failed.\nTraceback: {e}"

    return create_alert_message(error_message, color="warning")
