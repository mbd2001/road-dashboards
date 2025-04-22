import copy
import json
import os
import traceback

import pandas as pd
from botocore.exceptions import ClientError
from cloud_storage_utils.file_abstraction import open_file
from dash import Input, Output, State, callback, no_update
from road_database_toolkit.cloud_file_system.file_operations import write_json

from road_dashboards.road_eval_dashboard.components.components_ids import (
    MD_COLUMNS_TO_TYPE,
    MD_FILTERS,
    NETS,
    PATHNET_BOUNDARIES,
    PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD,
    PATHNET_DYNAMIC_THRESHOLD_OOL,
    PATHNET_DYNAMIC_THRESHOLD_RE_OOL,
    PATHNET_EVENTS_BOOKMARKS_JSON,
    PATHNET_EVENTS_CHOSEN_NET,
    PATHNET_EVENTS_CLIPS_UNIQUE_SWITCH,
    PATHNET_EVENTS_DATA_TABLE,
    PATHNET_EVENTS_DIST_DROPDOWN,
    PATHNET_EVENTS_DIST_DROPDOWN_DIV,
    PATHNET_EVENTS_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_EVENTS_ORDER_BY,
    PATHNET_EVENTS_EVENTS_ORDER_BY_DIV,
    PATHNET_EVENTS_EXCLUDE_NONE_SWITCH,
    PATHNET_EVENTS_EXTRACTOR_DICT,
    PATHNET_EVENTS_METRIC_DROPDOWN,
    PATHNET_EVENTS_NET_ID_DROPDOWN,
    PATHNET_EVENTS_NUM_EVENTS,
    PATHNET_EVENTS_RE_REF_THRESHOLD,
    PATHNET_EVENTS_RE_SWITCH,
    PATHNET_EVENTS_RE_SWITCH_DIV,
    PATHNET_EVENTS_RE_THRESHOLD,
    PATHNET_EVENTS_RE_THRESHOLDS_DIV,
    PATHNET_EVENTS_REF_CHOSEN_NET,
    PATHNET_EVENTS_REF_DIV,
    PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN,
    PATHNET_EVENTS_REF_NET_ID_DROPDOWN,
    PATHNET_EVENTS_REF_THRESHOLD,
    PATHNET_EVENTS_ROLE_DROPDOWN,
    PATHNET_EVENTS_ROLE_DROPDOWN_DIV,
    PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN,
    PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN_DIV,
    PATHNET_EVENTS_SUBMIT_BUTTON,
    PATHNET_EVENTS_THRESHOLD,
    PATHNET_EVENTS_THRESHOLDS_DIV,
    PATHNET_EVENTS_UNIQUE_SWITCH,
    PATHNET_EXPLORER_DATA,
    PATHNET_EXPORT_TO_BOOKMARK_BUTTON,
    PATHNET_EXPORT_TO_JUMP_BUTTON,
    PATHNET_EXTRACT_EVENTS_LOG_MESSAGE,
    PATHNET_GT,
    PATHNET_PRED,
)
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_avail_query,
    generate_extract_acc_events_query,
    generate_extract_miss_false_events_query,
    generate_extract_ool_events_query,
    generate_extract_roles_events_query,
    run_query_with_nets_names_processing,
)
from road_dashboards.road_eval_dashboard.utils.url_state_utils import create_alert_message, create_dropdown_options_list

BOOKMARKS_COLUMNS = ["clip_name", "grabindex"]
EXPLORER_PARAMS = """ 
    --dataset_names {dataset} 
    --population {population} 
    --bookmarks {bookmarks_name}
    --net_name {net_id} 
    --ckpt {checkpoint} 
    --use_case {use_case}  
"""
EXPLORER_PARAMS_REF_ADDITION = """--net_name {net_id} 
                                  --ckpt {checkpoint} 
                                  --use_case {use_case} 
"""
S3_EVENTS_DIR = (
    "s3://mobileye-team-road/roade2e_database/run_eval_catalog/{net_id}/{checkpoint}/{use_case}/{dataset}/events"
)
DEFAULT_NUM_EVENTS = 60
REF_THRESH_DEFAULT_DIFF = 0.1


@callback(
    Output(PATHNET_EVENTS_NET_ID_DROPDOWN, "options"),
    Output(PATHNET_EVENTS_REF_NET_ID_DROPDOWN, "options"),
    Input(NETS, "data"),
)
def get_eval_name(nets):
    net_options_list = create_dropdown_options_list(nets["names"]) if nets else no_update
    return net_options_list, net_options_list


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
    Output(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "options"),
    Input(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(MD_FILTERS, "data"),
    prevent_initial_call=True,
)
def create_dp_source_dropdown_main(net, meta_data_filters):
    return create_dp_source_dropdown(net, meta_data_filters)


@callback(
    Output(PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN, "options"),
    Input(PATHNET_EVENTS_REF_CHOSEN_NET, "data"),
    State(MD_FILTERS, "data"),
    prevent_initial_call=True,
)
def create_dp_source_dropdown_ref(net, meta_data_filters):
    return create_dp_source_dropdown(net, meta_data_filters)


def update_chosen_net_data(nets, chosen_net_id):
    if not nets or not chosen_net_id:
        return no_update

    net = copy.deepcopy(nets)
    net_id_ind = [i for i, net_id in enumerate(nets["names"]) if net_id == chosen_net_id][0]
    net["names"] = net["names"][net_id_ind : net_id_ind + 1]
    net["frame_tables"]["paths"] = net["frame_tables"]["paths"][net_id_ind : net_id_ind + 1]
    net[PATHNET_PRED]["paths"] = net[PATHNET_PRED]["paths"][net_id_ind : net_id_ind + 1]
    net[PATHNET_GT]["paths"] = net[PATHNET_GT]["paths"][net_id_ind : net_id_ind + 1]
    if net[PATHNET_BOUNDARIES]["paths"]:
        net[PATHNET_BOUNDARIES]["paths"] = net[PATHNET_BOUNDARIES]["paths"][net_id_ind : net_id_ind + 1]
    net["nets_info"] = net["nets_info"][net_id_ind]
    return net


@callback(
    Output(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(NETS, "data"),
    Input(PATHNET_EVENTS_NET_ID_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_chosen_net_data_main(nets, chosen_net_id):
    return update_chosen_net_data(nets, chosen_net_id)


@callback(
    Output(PATHNET_EVENTS_REF_CHOSEN_NET, "data"),
    State(NETS, "data"),
    Input(PATHNET_EVENTS_REF_NET_ID_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_chosen_net_data_ref(nets, chosen_net_id):
    return update_chosen_net_data(nets, chosen_net_id)


def get_mandatory_args(events_extractor_dict):
    metric = events_extractor_dict["metric"]
    mandatory_args = [events_extractor_dict["net"], events_extractor_dict["dp_source"], metric]
    if metric == "inaccurate":
        mandatory_args += [events_extractor_dict["role"], events_extractor_dict["dist"]]
    elif metric == "miss":
        mandatory_args.append(events_extractor_dict["role"])
    if events_extractor_dict["is_unique_on"]:
        mandatory_args += [events_extractor_dict["ref_net"], events_extractor_dict["ref_dp_source"]]
    return mandatory_args


def check_build_events_input(meta_data_columns, events_extractor_dict):
    if not all(mandatory_column in meta_data_columns for mandatory_column in BOOKMARKS_COLUMNS):
        return False, f"meta-data is missing one of {BOOKMARKS_COLUMNS} columns"

    mandatory_args = get_mandatory_args(events_extractor_dict)
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


def create_data_dict_for_explorer(events_extractor_dict, dp_sources):
    net_info = events_extractor_dict["net"]["nets_info"]
    s3_dir_path = S3_EVENTS_DIR.format(
        dataset=net_info["dataset"],
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
    )

    metric = events_extractor_dict["metric"]
    dp_source = events_extractor_dict["dp_source"]
    role = events_extractor_dict["role"]
    dist = events_extractor_dict["dist"]
    bookmarks_file_name = f"{metric}_{dp_source}"
    if metric != "false":
        bookmarks_file_name += f"_{role}"
    if metric in ["inaccurate", "out-of-lane"]:
        bookmarks_file_name += f"_dist{dist}"

    explorer_params = EXPLORER_PARAMS.format(
        dataset=net_info["dataset"],
        population=net_info["population"],
        bookmarks_name=bookmarks_file_name,
        net_id=net_info["net_id"],
        checkpoint=net_info["checkpoint"],
        use_case=net_info["use_case"],
    )

    if events_extractor_dict["is_unique_on"] and events_extractor_dict["ref_net"] != events_extractor_dict["net"]:
        ref_net_info = events_extractor_dict["ref_net"]["nets_info"]
        explorer_params += EXPLORER_PARAMS_REF_ADDITION.format(
            net_id=ref_net_info["net_id"], checkpoint=ref_net_info["checkpoint"], use_case=ref_net_info["use_case"]
        )

    dp_sources = {dic["label"] for dic in dp_sources}
    if "mf" in dp_sources:
        explorer_params += " --net_output_name mf"
    elif "fusion" in dp_sources:
        explorer_params += " --net_output_name fusion"

    return {"s3_dir_path": s3_dir_path, "bookmarks_name": bookmarks_file_name, "explorer_params": explorer_params}


def get_source_events_df(
    net,
    dp_source,
    meta_data_filters,
    metric,
    role,
    dist,
    threshold,
    re_threshold,
    re_only,
    order_by,
    is_ref=False,
    semantic_role=None,
    exclude_none=False,
    extra_columns=[],
):
    bookmarkes_columns = BOOKMARKS_COLUMNS + extra_columns
    if metric == "inaccurate":
        operator = ">" if not is_ref else "<"
        query, final_columns = generate_extract_acc_events_query(
            data_tables=net[PATHNET_PRED],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=bookmarkes_columns,
            chosen_source=dp_source,
            role=role,
            dist=float(dist),
            threshold=threshold,
            operator=operator,
            order_by=order_by,
        )
    elif metric == "out-of-lane":
        operator = "<" if not is_ref else ">"
        query, final_columns = generate_extract_ool_events_query(
            data_tables=net[PATHNET_BOUNDARIES],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=bookmarkes_columns,
            chosen_source=dp_source,
            role=role,
            dist=float(dist),
            threshold=threshold,
            re_threshold=re_threshold,
            operator=operator,
            order_by=order_by,
            re_only=re_only,
        )
    elif metric == "role":
        query, final_columns = generate_extract_roles_events_query(
            data_tables=net[PATHNET_PRED],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=bookmarkes_columns,
            chosen_source=dp_source,
            role=role,
            semantic_role=semantic_role,
            exclude_none=exclude_none,
        )
    else:  # metric is false/miss
        query, final_columns = generate_extract_miss_false_events_query(
            data_tables=net[PATHNET_PRED] if metric == "false" else net[PATHNET_GT],
            meta_data=net["meta_data"],
            meta_data_filters=meta_data_filters,
            bookmarks_columns=bookmarkes_columns,
            chosen_source=dp_source,
            role="unmatched-non-host" if metric == "false" else f"unmatched-{role}",
        )

    df, _ = run_query_with_nets_names_processing(query)
    df = df.drop_duplicates(subset=final_columns)
    return df


def subtract_events(df_main, df_ref, metric):
    if metric == "miss":
        merge_df = df_main.merge(df_ref, how="left", indicator=True)
        only_in_main_df = merge_df[merge_df["_merge"] == "left_only"]
        only_in_main_df = only_in_main_df.drop(columns=["_merge"])
        return only_in_main_df

    elif metric == "false":
        df_main_grouped = df_main.groupby(BOOKMARKS_COLUMNS).size().reset_index(name="count_main")
        df_ref_grouped = df_ref.groupby(BOOKMARKS_COLUMNS).size().reset_index(name="count_ref")
        frames_count_df = df_main_grouped.merge(df_ref_grouped, on=BOOKMARKS_COLUMNS, how="left")
        frames_count_df["count_ref"].fillna(0, inplace=True)
        frames_count_higher_in_main_df = frames_count_df[frames_count_df["count_main"] > frames_count_df["count_ref"]]
        df_main_filtered = df_main.merge(frames_count_higher_in_main_df[BOOKMARKS_COLUMNS], on=BOOKMARKS_COLUMNS)
        return df_main_filtered

    elif metric == "inaccurate":
        df_main_filtered = df_main.merge(
            df_ref, on=BOOKMARKS_COLUMNS + ["matched_dp_id"], how="inner", suffixes=("", "_ref")
        )
        return df_main_filtered

    elif metric == "out-of-lane":
        df_main_filtered = df_main.merge(df_ref, on=BOOKMARKS_COLUMNS + ["dp_id"], how="inner", suffixes=("", "_ref"))
        df_main_filtered.drop(columns=[c for c in df_main_filtered.columns if "closer" in c], inplace=True)
        return df_main_filtered

    else:
        return df_main


def get_events_df(
    events_extractor_dict,
    meta_data_cols,
    meta_data_filters,
):
    if "frame_has_labels_mf" in meta_data_cols:
        meta_data_filters = "frame_has_labels_mf = 1" + (f" AND ({meta_data_filters})" if meta_data_filters else "")
    metric = events_extractor_dict["metric"]
    role = events_extractor_dict["role"]
    semantic_role = events_extractor_dict["semantic_role"]
    dist = events_extractor_dict["dist"]
    df = get_source_events_df(
        events_extractor_dict["net"],
        events_extractor_dict["dp_source"],
        meta_data_filters,
        metric,
        role,
        dist,
        events_extractor_dict["threshold"],
        events_extractor_dict["re_threshold"],
        events_extractor_dict["re_only"],
        events_extractor_dict["order_by"],
        semantic_role=semantic_role,
        exclude_none=events_extractor_dict["exclude_none"],
        extra_columns=events_extractor_dict["extra_columns"],
    )

    if events_extractor_dict["is_unique_on"]:
        df_ref = get_source_events_df(
            events_extractor_dict["ref_net"],
            events_extractor_dict["ref_dp_source"],
            meta_data_filters,
            metric,
            role,
            dist,
            events_extractor_dict["ref_threshold"],
            events_extractor_dict["ref_re_threshold"],
            events_extractor_dict["re_only"],
            events_extractor_dict["order_by"],
            semantic_role=semantic_role,
            is_ref=True,
            exclude_none=events_extractor_dict["exclude_none"],
            extra_columns=events_extractor_dict["extra_columns"],
        )
        df = subtract_events(df, df_ref, metric)

    if events_extractor_dict["clips_unique_on"]:
        df = df.drop_duplicates("clip_name", keep="first")

    df = df.head(events_extractor_dict["num_events"])
    df = df.round(3)
    return df


@callback(
    Output(PATHNET_EVENTS_ROLE_DROPDOWN_DIV, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_events_role_dropdown(metric):
    return metric == "false"


@callback(
    Output(PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN_DIV, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_role_and_semantic_dropdown(metric):
    if metric == "role":
        return False
    return True


@callback(
    Output(PATHNET_EVENTS_EXCLUDE_NONE_SWITCH, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_exclude_none_dropdown(metric):
    if metric == "role":
        return False
    return True


@callback(
    Output(PATHNET_EVENTS_DIST_DROPDOWN_DIV, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_events_dist_dropdown(metric):
    if metric in ["inaccurate", "out-of-lane"]:
        return False
    return True


@callback(
    Output(PATHNET_EVENTS_EVENTS_ORDER_BY_DIV, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_events_order_by_dropdown(metric):
    if metric in ["inaccurate", "out-of-lane"]:
        return False
    return True


@callback(
    Output(PATHNET_EVENTS_RE_SWITCH_DIV, "hidden"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def show_events_ool_re_switch(metric):
    return metric != "out-of-lane"


@callback(
    Output(PATHNET_EVENTS_REF_DIV, "hidden"),
    Output(PATHNET_EVENTS_THRESHOLDS_DIV, "hidden"),
    Output(PATHNET_EVENTS_RE_THRESHOLDS_DIV, "hidden"),
    Input(PATHNET_EVENTS_UNIQUE_SWITCH, "on"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    Input(PATHNET_EVENTS_RE_SWITCH, "on"),
    prevent_initial_call=True,
)
def show_unique_choices(is_unique_on, metric, is_re_only):
    hide_ref_div = not is_unique_on
    show_thresholds_div = is_unique_on and (metric == "inaccurate" or (metric == "out-of-lane" and not is_re_only))
    hide_thresholds_div = not show_thresholds_div
    show_re_thresholds_div = is_unique_on and metric == "out-of-lane"
    hide_re_thresholds_div = not show_re_thresholds_div
    return hide_ref_div, hide_thresholds_div, hide_re_thresholds_div


@callback(
    Output(PATHNET_EVENTS_THRESHOLD, "placeholder"),
    Output(PATHNET_EVENTS_REF_THRESHOLD, "placeholder"),
    Output(PATHNET_EVENTS_RE_THRESHOLD, "placeholder"),
    Output(PATHNET_EVENTS_RE_REF_THRESHOLD, "placeholder"),
    Input(PATHNET_EVENTS_UNIQUE_SWITCH, "on"),
    Input(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    Input(PATHNET_EVENTS_DIST_DROPDOWN, "value"),
    Input(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    Input(PATHNET_DYNAMIC_THRESHOLD_OOL, "data"),
    Input(PATHNET_DYNAMIC_THRESHOLD_RE_OOL, "data"),
    prevent_initial_call=True,
)
def get_specified_thresholds_placeholders(
    is_unique_on, metric, dist, thresh_dict, ool_min_border_dist_dict, ool_min_re_dist_dict
):
    if not is_unique_on or metric not in ["inaccurate", "out-of-lane"]:
        return "", "", "", ""

    if metric == "inaccurate":
        main_th_ph = "Specify acc-threshold in meters (optional)"
        ref_th_ph = "Specify ref acc-threshold in meters (optional)"
        if dist:
            main_default_th = thresh_dict[str(float(dist))]
            main_th_ph += f", default = {main_default_th:.2f}"
            ref_th_ph += f", default = {(main_default_th - REF_THRESH_DEFAULT_DIFF):.2f}"
        return main_th_ph, ref_th_ph, "", ""

    main_th_ph = "Specify dp-border min-dist in meters (optional)"
    ref_th_ph = "Specify ref dp-border min-dist in meters (optional)"
    main_re_th_ph = "Specify dp-roadedge min-dist in meters (optional)"
    ref_re_th_ph = "Specify ref dp-roadedge min-dist in meters (optional)"

    if dist:
        ool_min_border_dist = ool_min_border_dist_dict[str(float(dist))]
        ool_min_re_dist = ool_min_re_dist_dict[str(float(dist))]
        main_th_ph += f", default = {ool_min_border_dist:.2f}"
        ref_th_ph += f", default = {(ool_min_border_dist + REF_THRESH_DEFAULT_DIFF):.2f}"
        main_re_th_ph += f", default = {ool_min_re_dist:.2f}"
        ref_re_th_ph += f", default = {(ool_min_re_dist + REF_THRESH_DEFAULT_DIFF):.2f}"

    return main_th_ph, ref_th_ph, main_re_th_ph, ref_re_th_ph


@callback(
    Output(PATHNET_EVENTS_EXTRACTOR_DICT, "data"),
    Input(PATHNET_EVENTS_SUBMIT_BUTTON, "n_clicks"),
    State(PATHNET_EVENTS_EXTRACTOR_DICT, "data"),
    State(PATHNET_EVENTS_CHOSEN_NET, "data"),
    State(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_METRIC_DROPDOWN, "value"),
    State(PATHNET_EVENTS_ROLE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_DIST_DROPDOWN, "value"),
    State(PATHNET_EVENTS_UNIQUE_SWITCH, "on"),
    State(PATHNET_EVENTS_REF_CHOSEN_NET, "data"),
    State(PATHNET_EVENTS_REF_DP_SOURCE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_NUM_EVENTS, "value"),
    State(PATHNET_EVENTS_THRESHOLD, "value"),
    State(PATHNET_EVENTS_REF_THRESHOLD, "value"),
    State(PATHNET_DYNAMIC_DISTANCE_TO_THRESHOLD, "data"),
    State(PATHNET_EVENTS_EVENTS_ORDER_BY, "value"),
    State(PATHNET_EVENTS_CLIPS_UNIQUE_SWITCH, "on"),
    Input(PATHNET_DYNAMIC_THRESHOLD_OOL, "data"),
    Input(PATHNET_DYNAMIC_THRESHOLD_RE_OOL, "data"),
    State(PATHNET_EVENTS_RE_THRESHOLD, "value"),
    State(PATHNET_EVENTS_RE_REF_THRESHOLD, "value"),
    State(PATHNET_EVENTS_RE_SWITCH, "on"),
    State(PATHNET_EVENTS_SEMANTIC_ROLE_DROPDOWN, "value"),
    State(PATHNET_EVENTS_EXCLUDE_NONE_SWITCH, "on"),
    Input("pathnet-events-extra-columns-dropdown", "value"),
    prevent_initial_call=True,
)
def update_extractor_dict(
    n_clicks,
    events_extractor_dict,
    net,
    dp_source,
    metric,
    role,
    dist,
    is_unique_on,
    ref_net,
    ref_dp_source,
    num_events,
    specified_thresh,
    ref_specified_thresh,
    thresh_dict,
    order_by,
    clips_unique_on,
    ool_min_border_dist_dict,
    ool_min_re_dist_dict,
    specified_re_thresh,
    ref_specified_re_thresh,
    is_re_switch_on,
    semantic_role,
    exclude_none,
    extra_columns,
):
    if not n_clicks:
        return events_extractor_dict

    events_extractor_dict["net"] = net
    events_extractor_dict["dp_source"] = dp_source
    events_extractor_dict["metric"] = metric
    events_extractor_dict["role"] = role
    events_extractor_dict["dist"] = dist
    events_extractor_dict["is_unique_on"] = is_unique_on
    events_extractor_dict["ref_net"] = ref_net
    events_extractor_dict["ref_dp_source"] = ref_dp_source
    events_extractor_dict["semantic_role"] = semantic_role
    events_extractor_dict["exclude_none"] = exclude_none
    events_extractor_dict["num_events"] = num_events if num_events is not None else DEFAULT_NUM_EVENTS
    events_extractor_dict["extra_columns"] = extra_columns or []
    if specified_thresh is not None:
        events_extractor_dict["threshold"] = specified_thresh
    elif dist is not None:
        events_extractor_dict["threshold"] = (
            ool_min_border_dist_dict[str(float(dist))] if metric == "out-of-lane" else thresh_dict[str(float(dist))]
        )
    else:
        events_extractor_dict["threshold"] = 0

    if specified_re_thresh is not None:
        events_extractor_dict["re_threshold"] = specified_re_thresh
    elif dist is not None:
        events_extractor_dict["re_threshold"] = ool_min_re_dist_dict[str(float(dist))]
    else:
        events_extractor_dict["re_threshold"] = 0

    if is_unique_on:
        if ref_specified_thresh is not None:
            events_extractor_dict["ref_threshold"] = ref_specified_thresh
        elif metric == "out-of-lane":
            events_extractor_dict["ref_threshold"] = events_extractor_dict["threshold"] + REF_THRESH_DEFAULT_DIFF
        else:
            events_extractor_dict["ref_threshold"] = events_extractor_dict["threshold"] - REF_THRESH_DEFAULT_DIFF

        if ref_specified_re_thresh is not None:
            events_extractor_dict["ref_re_threshold"] = ref_specified_re_thresh
        elif metric == "out-of-lane":
            events_extractor_dict["ref_re_threshold"] = events_extractor_dict["re_threshold"] + REF_THRESH_DEFAULT_DIFF
        else:
            events_extractor_dict["ref_re_threshold"] = 0

    default_order_by = "ASC" if metric == "out-of-lane" else "DESC"
    events_extractor_dict["order_by"] = order_by if order_by is not None else default_order_by
    events_extractor_dict["clips_unique_on"] = clips_unique_on

    events_extractor_dict["re_only"] = is_re_switch_on

    return events_extractor_dict


@callback(
    Output(PATHNET_EVENTS_DATA_TABLE, "data"),
    Output(PATHNET_EVENTS_DATA_TABLE, "columns"),
    Output(PATHNET_EVENTS_BOOKMARKS_JSON, "data"),
    Output(PATHNET_EXPLORER_DATA, "data"),
    Output(PATHNET_EXTRACT_EVENTS_LOG_MESSAGE, "children"),
    Input(PATHNET_EVENTS_EXTRACTOR_DICT, "data"),
    State(PATHNET_EVENTS_SUBMIT_BUTTON, "n_clicks"),
    State(PATHNET_EVENTS_DP_SOURCE_DROPDOWN, "options"),
    State(MD_FILTERS, "data"),
    State(MD_COLUMNS_TO_TYPE, "data"),
    prevent_initial_call=True,
)
def build_events_df(
    events_extractor_dict,
    n_clicks,
    dp_sources,
    meta_data_filters,
    meta_data_cols,
):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, create_alert_message("", color="warning")

    input_valid, input_error_message = check_build_events_input(meta_data_cols, events_extractor_dict)
    if not input_valid:
        return no_update, no_update, no_update, no_update, create_alert_message(input_error_message, color="warning")

    df = get_events_df(events_extractor_dict, meta_data_cols, meta_data_filters)
    df_sane, sanity_error_message = check_events_df_sanity(events_df=df)
    if not df_sane:
        return no_update, no_update, no_update, no_update, create_alert_message(sanity_error_message, color="warning")

    bookmarks_json = converts_events_df_to_bookmarks_json(events_df=df)
    data_for_explorer = create_data_dict_for_explorer(events_extractor_dict, dp_sources)

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
    explorer_params = explorer_data["explorer_params"]

    s3_full_path = os.path.join(s3_dir_path, f"{bookmarks_file_name}.json")
    try:
        write_json(s3_full_path, bookmarks_dict)
        success_message = f"Bookmarks dumped to:\n{s3_full_path}\n\nParams for explorer: {explorer_params}"
        return create_alert_message(success_message, color="success")

    except (json.JSONDecodeError, TypeError) as e:
        error_message = f"Invalid to decode json format.\nTraceback: {e}"
    except ClientError as e:
        error_message = f"Error uploading to S3:\n'{s3_full_path}' failed.\nTraceback: {e}"

    return create_alert_message(error_message, color="warning")


@callback(
    Output("pathnet-events-extra-columns-dropdown", "options"),
    Input(MD_COLUMNS_TO_TYPE, "data"),
)
def fill_extra_column_dropdown(md_columns):
    if not md_columns:
        return no_update
    return [{"label": col, "value": col} for col in md_columns]


@callback(
    Output(PATHNET_EXTRACT_EVENTS_LOG_MESSAGE, "children", allow_duplicate=True),
    Input(PATHNET_EXPORT_TO_JUMP_BUTTON, "n_clicks"),
    State(PATHNET_EVENTS_DATA_TABLE, "data"),
    State(PATHNET_EXPLORER_DATA, "data"),
    prevent_initial_call=True,
)
def dump_events_to_jump(n_clicks, data_table, explorer_data):
    if not all([n_clicks, data_table, explorer_data]):
        return no_update

    s3_dir_path = explorer_data["s3_dir_path"]
    bookmarks_file_name = explorer_data["bookmarks_name"]

    s3_full_path = os.path.join(s3_dir_path, f"{bookmarks_file_name}.jump")
    try:
        df = pd.DataFrame(data_table)
        cols_with_dot = [col for col in df.columns if "." in col]
        df_renamed = df.rename(columns={col: col.replace(".", "_") for col in cols_with_dot}, inplace=False)
        generate_jump_file(df_renamed, s3_full_path, df_renamed.columns.to_list(), df.size)
        success_message = f"Jump dumped to:\n{s3_full_path}\n"
        return create_alert_message(success_message, color="success")

    except Exception:
        error_message = f"Error genereting jump into:\n'{s3_full_path}' failed.\nTraceback: {traceback.format_exc()}"

    return create_alert_message(error_message, color="warning")


def generate_jump_file(df, out_jump_file_path, more_fields, max_lines=300, clipname_to_itrk_location_fn=lambda x: x):
    clip_field, gi_field = "clip_name", "grabindex"
    jump_fields = [gi_field] + list(set(more_fields) - set([clip_field, gi_field]))  # ordered
    all_clips = []
    with open_file(out_jump_file_path, "w") as f:
        for row in df.head(max_lines).itertuples():
            clipname = getattr(row, clip_field)
            if clipname is None:
                continue
            all_clips.append(clipname)
            line = "{}".format(clipname_to_itrk_location_fn(clipname))
            for field in jump_fields:
                val = getattr(row, field)
                if type(val) == float:
                    val = "{:.2f}".format(val)
                line += f" {val}"
            f.write(line + "\n")
        format_line = "\n#format: trackfile startframe " + " ".join(jump_fields[1:])
        f.write(format_line + "\n")
    # also dump a list of all clips
    with open_file(out_jump_file_path + ".list", "w") as f:
        f.write("\n".join(list(set(all_clips))))
