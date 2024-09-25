import copy
import json

from botocore.exceptions import ClientError
from dash import Input, Output, State, callback, no_update
from road_database_toolkit.cloud_file_system.file_operations import path_join, write_json

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NETS,
    PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD,
    PATHNET_EVENTS_BOOKMARKS_JSON,
    PATHNET_EVENTS_CHOSEN_NET,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_EVENTS_ORDER_BY,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EXPLORER_DATA,
    PATHNET_EXPORT_TO_BOOKMARK_BUTTON,
    PATHNET_EXPORT_TO_JUMP_BUTTON,
    PATHNET_EXTRACT_EVENTS_LOG_MESSAGE,
    PATHNET_GT,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_avail_query,
    generate_extract_inacc_events_query,
    generate_extract_miss_false_events_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_alert_message, create_dropdown_options_list

BOOKMARKS_COLUMNS = ["batch_num", "clip_name", "grabindex"]
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

    if not all(mandatory_column in meta_data_columns for mandatory_column in BOOKMARKS_COLUMNS):
        return False, f"meta-data is missing one of {BOOKMARKS_COLUMNS} columns"

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
    df_as_bookmarks = events_df[BOOKMARKS_COLUMNS]

    comment_columns = [col for col in events_df.columns if col not in BOOKMARKS_COLUMNS]

    df_as_bookmarks["comment"] = events_df[comment_columns].apply(
        lambda row: "; ".join(f"{col}={val}" for col, val in row.items()), axis=1
    )

    return df_as_bookmarks.to_dict(orient="split")["data"]


def create_data_dict_for_explorer(net_info, dp_sources, chosen_source, role, dist, metric):
    s3_dir_path = S3_EVENTS_DIR.format(
        dataset=net_info["dataset"],
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
    )
    bookmarks_file_name = f"{metric}_{chosen_source}_{role}_dist{dist}"
    explorer_params = EXPLORER_PARAMS.format(
        dataset=net_info["dataset"],
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
        population=net_info["population"],
        bookmarks_name=bookmarks_file_name,
    )
    dp_sources = {dic["label"] for dic in dp_sources}

    if "mf" in dp_sources:
        explorer_params += " --net_output_name mf"
    elif "fusion" in dp_sources:
        explorer_params += " --net_output_name fusion"

    return {"s3_dir_path": s3_dir_path, "bookmarks_name": bookmarks_file_name, "explorer_params": explorer_params}


def get_events_df(
    chosen_source, meta_data_cols, meta_data_filters, metric, net, role, samples_num, dist, threshold, order_by
):
    DEFAULT_SAMPLES_NUM = 60
    if "frame_has_labels_mf" in meta_data_cols:
        meta_data_filters = "frame_has_labels_mf = 1" + (f" AND ({meta_data_filters})" if meta_data_filters else "")

    if metric == "inaccurate":
        query, final_columns = generate_extract_inacc_events_query(
            data_tables=net[PATHNET_PRED],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=BOOKMARKS_COLUMNS,
            chosen_source=chosen_source,
            role=role,
            dist=float(dist),
            threshold=threshold,
            order_by=order_by,
        )
    else:  # metric is false/miss
        query, final_columns = generate_extract_miss_false_events_query(
            data_tables=net[PATHNET_PRED] if metric == "false" else net[PATHNET_GT],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=BOOKMARKS_COLUMNS,
            chosen_source=chosen_source,
            role="unmatched-non-host" if metric == "false" else f"unmatched-{role}",
        )

    df, _ = run_query_with_nets_names_processing(query)
    df = df.drop_duplicates(subset=final_columns)
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
    State(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "options"),
    Input(PATHNET_EVENTS_SUBMIT_BUTTON, "n_clicks"),
    State(MD_FILTERS, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
    State(PATHNET_EVENTS_ROLE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_DIST_DROPDOWN, "value"),
    State(PATHNET_EVENTS_EVENTS_ORDER_BY, "value"),
    State(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    State(PATHNET_EVENTS_NUM_EVENTS, "value"),
    State(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    prevent_initial_call=True,
)
def build_events_df(
    net,
    chosen_source,
    dp_sources,
    n_clicks,
    meta_data_filters,
    meta_data_cols,
    role,
    dist,
    order_by,
    metric,
    samples_num,
    thresh_dict,
):
    dropdown_args = [net, chosen_source, metric]
    if metric == "inaccurate":
        dropdown_args += [role, dist]
    elif metric == "miss":
        dropdown_args.append(role)

    input_valid, input_error_message = check_build_events_input(n_clicks, meta_data_cols, dropdown_args)
    if not input_valid:
        return no_update, no_update, no_update, no_update, create_alert_message(input_error_message, color="warning")

    thresh = thresh_dict[str(float(dist))] if dist is not None else 0
    df = get_events_df(
        chosen_source, meta_data_cols, meta_data_filters, metric, net, role, samples_num, dist, thresh, order_by
    )
    df_sane, sanity_error_message = check_events_df_sanity(events_df=df)
    if not df_sane:
        return no_update, no_update, no_update, no_update, create_alert_message(sanity_error_message, color="warning")

    bookmarks_json = converts_events_df_to_bookmarks_json(events_df=df)
    data_for_explorer = create_data_dict_for_explorer(net["nets_info"], dp_sources, chosen_source, role, dist, metric)

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


@callback(
    Output(PATHNET_EXTRACT_EVENTS_LOG_MESSAGE, "children", allow_duplicate=True),
    Input(PATHNET_EXPORT_TO_JUMP_BUTTON, "n_clicks"),
    State(PATHNET_EVENTS_DATA_TABLE, "data"),
    State(PATHNET_EXPLORER_DATA, "data"),
    prevent_initial_call=True,
)
def dump_events_to_jump(n_clicks, data_table, explorer_data):
    import traceback

    import pandas as pd

    if not all([n_clicks, data_table, explorer_data]):
        return no_update

    s3_dir_path = explorer_data["s3_dir_path"]
    bookmarks_file_name = explorer_data["bookmarks_name"]

    s3_full_path = path_join(s3_dir_path, f"{bookmarks_file_name}.jump")
    try:
        df = pd.DataFrame(data_table)
        cols_with_dot = [col for col in df.columns if "." in col]
        df_renamed = df.rename(columns={col: col.replace(".", "_") for col in cols_with_dot}, inplace=False)
        generate_jump_file(df_renamed, s3_full_path, df_renamed.columns.to_list(), df.size)
        success_message = f"Jump dumped to:\n{s3_full_path}\n"
        return create_alert_message(success_message, color="success")

    except Exception as e:
        error_message = f"Error genereting jump into:\n'{s3_full_path}' failed.\nTraceback: {traceback.format_exc()}"

    return create_alert_message(error_message, color="warning")


def generate_jump_file(df, out_jump_file_path, more_fields, max_lines=300, clipname_to_itrk_location_fn=lambda x: x):
    import numpy as np
    from cloud_storage_utils.file_abstraction import open_file

    def _is_float(val):
        return (
            (getattr(val, "dtype", "int") != np.int64)
            and (getattr(val, "dtype", "int") != np.int32)
            and (
                (getattr(val, "dtype", "int") == np.float32)
                or (getattr(val, "dtype", "int") == np.float64)
                or (type(val) == float)
            )
        )

    if "clip_name" in df:
        _get_clipname = lambda row: getattr(row, "clip_name")
    else:
        assert "no clipname field in df"

    if "grabindex" in df:
        gi_field = "grabindex"
    elif "gi" in df:
        gi_field = "gi"
    else:
        assert "no grabIndex field in df"

    jump_fields = list(set([gi_field] + more_fields))
    all_clips = []
    with open_file(out_jump_file_path, "w") as f:
        for row in df.head(max_lines).itertuples():
            clipname = _get_clipname(row)
            if clipname is None:
                continue
            all_clips.append(clipname)
            line = "{}".format(clipname_to_itrk_location_fn(clipname))
            for field in jump_fields:
                val = getattr(row, field)
                if type(val) == np.ndarray:
                    val = val.squeeze()
                if _is_float(val):
                    val = "{:.2f}".format(val)
                line += f" {val}"
            f.write(line + "\n")
        format_line = "\n#format: trackfile startframe " + " ".join(jump_fields[1:])
        f.write(format_line + "\n")
    # also dump a list of all clips
    with open_file(out_jump_file_path + ".list", "w") as f:
        f.write("\n".join(list(set(all_clips))))
