import re
import s3fs
import json
import numpy as np
import dash_bootstrap_components as dbc
from dash_canvas.utils import array_to_data_url
from dash import callback, Output, Input, State, no_update
from natsort import natsorted

# from maffe_bins.road4.data.frame_data import FrameData
# from maffe_bins.road4.display.frame_drawer import FrameDrawer
from road_database_toolkit.athena.athena_utils import query_athena
from road_dump_dashboard.components.constants.components_ids import (
    DRAW_TVGT_DIFF_BTN,
    MD_FILTERS,
    TABLES,
    POPULATION_DROPDOWN,
    MAIN_NET_DROPDOWN,
    SECONDARY_NET_DROPDOWN,
)
from road_dump_dashboard.components.dashboard_layout.layout_wrappers import card_wrapper
from road_dump_dashboard.components.logical_components.queries_manager import generate_diff_query
from maffe_bins.road_db.drone_view_images.drone_view_db_manager import DroneViewDBManager
from maffe_bins.road4.road4_consts import CASide, LMColor, LMType, LM_ROLES, CAType

DV_DB_MANAGER = DroneViewDBManager()
json_path = "s3://mobileye-team-road/roade2e_database/artifacts/amosa20240311_ool_dist_per_point/bins.json"
with s3fs.S3FileSystem().open(json_path, "r") as f:
    json_info = json.load(f)


layout = dbc.Row(
    card_wrapper(
        [
            dbc.Carousel(
                id="carousel1",
                items=[],
                controls=True,
                indicators=False,
            ),
        ]
    )
)


@callback(
    Output("carousel1", "items"),
    Input(DRAW_TVGT_DIFF_BTN, "n_clicks"),
    Input(MD_FILTERS, "data"),
    State(TABLES, "data"),
    Input(POPULATION_DROPDOWN, "value"),
    Input(MAIN_NET_DROPDOWN, "value"),
    Input(SECONDARY_NET_DROPDOWN, "value"),
    background=True,
)
def draw_diffs(n_clicks, meta_data_filters, tables, population, main_dump, secondary_dump):
    if not n_clicks or not population or not tables or not main_dump or not secondary_dump:
        return no_update

    main_tables = tables["meta_data"]
    column_to_compare = "is_tv_perfect"
    query = generate_diff_query(
        main_dump,
        secondary_dump,
        main_tables,
        population,
        column_to_compare,
        meta_data_filters=meta_data_filters,
        labels_tables=tables["lm_meta_data"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)

    main_labels_df = split_df_columns_by_start_and_end(data, "main_start", "secondary_start")
    secondary_labels_df = split_df_columns_by_start_and_end(data, "secondary_start")
    main_lables_dict = parse_labels_df(main_labels_df)
    secondary_label_dict = parse_labels_df(secondary_labels_df)

    clip_names, grab_indexes = list(zip(*main_lables_dict.keys()))
    grab_indexes = [int(gi) for gi in grab_indexes]
    data_types = ["data"] * len(clip_names)

    images = DV_DB_MANAGER.load_images_multiple_clips(clip_names, grab_indexes, data_types)
    for clip_name, grab_index in zip(clip_names, grab_indexes):
        main_lables_dict[(clip_name, grab_index)]["data"] = images[clip_name]["data"][grab_index]
        secondary_label_dict[(clip_name, grab_index)]["data"] = images[clip_name]["data"][grab_index]

    # main_frames = [get_frame_ax(main_lables_dict, clip_name, grab_index) for clip_name, grab_index in main_lables_dict.keys()]
    # secondary_frames = [get_frame_ax(secondary_label_dict, clip_name, grab_index) for clip_name, grab_index in main_lables_dict.keys()]
    # return main_frames, secondary_frames

    combined_frames = [
        array_to_data_url(
            np.hstack((images[clip_name]["data"][grab_index][0][0], images[clip_name]["data"][grab_index][0][0]))
        )
        for clip_name, grab_index in zip(clip_names, grab_indexes)
    ]
    combined_frames = [{"key": i, "src": dat} for i, dat in enumerate(combined_frames)]
    return combined_frames


def split_df_columns_by_start_and_end(df, start_col, end_col=None):
    columns_to_return = []
    is_active = False
    for col in df.columns:
        if col == end_col:
            break
        if is_active:
            columns_to_return.append(col)
            continue
        if col == start_col:
            is_active = True

    return df[columns_to_return]


def parse_labels_df(labels_df):
    if labels_df.empty:
        return {}

    labels_df = labels_df.rename(columns=lambda x: re.sub(r"\.\d+$", "", x))
    labels_dict = {x: y.to_dict("list") for x, y in labels_df.groupby(["clip_name", "grabindex"])}
    labels_dict = {
        frame_id: parse_frame_labels_dict(frame_labels_dict) for frame_id, frame_labels_dict in labels_dict.items()
    }
    return labels_dict


def parse_frame_labels_dict(labels_dict):
    labels_dict = merge_partitioned_columns(labels_dict)
    labels_dict = {normalize_key_name(key): val for key, val in labels_dict.items()}
    return labels_dict


def merge_partitioned_columns(labels_dict):
    merged_labels_dict = {}
    for col in natsorted(labels_dict.keys()):
        col_val = labels_dict[col]
        if re.search(r"_\d+$", col):
            new_col = re.sub(r"_\d+$", "", col)
            if isinstance(col_val[0], str):
                col_val = [json.loads(coord) for coord in col_val]
            col_val = np.array(col_val)
            if col_val.ndim == 1:
                col_val = col_val.reshape(-1, 1)
            if new_col not in merged_labels_dict:
                merged_labels_dict[new_col] = col_val
            else:
                merged_labels_dict[new_col] = np.hstack((merged_labels_dict[new_col], col_val))
        else:
            merged_labels_dict[col] = np.array(col_val)

    return merged_labels_dict


def normalize_key_name(col):
    if col in ["grabindex", "clip_name"]:
        return col

    col = re.sub(r"(_[xyz])$", lambda m: m.group(1).upper(), col)
    col = f"lm_{col}"
    return col


def normalize_columns(df):
    cols_to_convert = {
        "vert_re_side": CASide,
        "vert_color": LMColor,
        "vert_type": LMType,
        "vert_role": LM_ROLES,
        "vert_re_type": CAType,
    }

    for col_name, enum_class in cols_to_convert.items():
        if col_name not in df.columns:
            continue

        if isinstance(enum_class, dict):
            df[col_name] = df[col_name].map(enum_class)
        else:
            df[col_name] = df[col_name].map(lambda x: safe_get_from_enum(enum_class=enum_class, x=x))
    return df


def safe_get_from_enum(enum_class, x):
    try:
        return enum_class[x].value
    except ValueError:
        return -1


# def get_frame_ax(frame_dict, grab_index, clip_name):
#     frame_data = FrameData.init_from_dict(
#         frame_pred=None,
#         frame_labels=frame_dict,
#         params_json_path=None,
#         img_size={"width": 513, "height": 256},
#         params_json=json_info,
#         shift_labels=False,
#         load_pred=False,
#         load_losses=False,
#         frame_idx=int(grab_index),
#         batch_num=0,
#         clip_name=clip_name,
#     )
#     frame_drawer = FrameDrawer(frame_data)
#     ax = frame_drawer.display_image()
#     frame_drawer.draw_labels(ax=ax)
#     return mpld3.fig_to_html(ax)
