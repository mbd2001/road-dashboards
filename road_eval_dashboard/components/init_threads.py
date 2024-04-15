from road_database_toolkit.athena.athena_utils import query_athena

from road_eval_dashboard.components.common_filters import ALL_FILTERS
from road_eval_dashboard.components.queries_manager import (
    generate_base_query,
    generate_cols_query,
    generate_fb_query,
    generate_grab_index_hist_query,
)
from road_eval_dashboard.graphs.precision_recall_curve import calc_best_thresh


def generate_meta_data_dicts(nets):
    md_columns_to_type = get_meta_data_columns(nets)
    distinct_dict = get_distinct_values_dict(nets, md_columns_to_type)

    md_columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in md_columns_to_type.keys()]
    md_columns_to_distinguish_values = {
        col: [{"label": val.strip(" "), "value": f"'{val.strip(' ')}'"} for val in val_list[0].strip("[]").split(",")]
        for col, val_list in distinct_dict.items()
    }

    return md_columns_to_type, md_columns_options, md_columns_to_distinguish_values


def generate_effective_samples_per_batch(nets):
    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    query = generate_grab_index_hist_query(tables_lists, meta_data, ALL_FILTERS)
    try:
        data, _ = query_athena(database="run_eval_db", query=query)
        effective_samples_per_batch = data.to_dict("records")[0]
        return effective_samples_per_batch
    except:
        print(
            "It seems like you're working with old dataset. In order to enjoy the full capabilites of the dashboard please re-run the 'parquets_converter_cfg' and 'generate_meta_data_table' stages of the dump."
        )
        return {}


def get_meta_data_columns(nets):
    query = f"SELECT * FROM {nets['meta_data']} LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    md_columns_to_type = dict(data.dtypes.apply(lambda x: x.name))
    return md_columns_to_type


def get_distinct_values_dict(nets, md_columns_to_type):
    distinct_select = ",".join(
        [
            f' array_agg(DISTINCT "{col}") AS "{col}" '
            for col in md_columns_to_type.keys()
            if md_columns_to_type[col] == "object"
        ]
    )
    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    base_query = generate_base_query(tables_lists, meta_data)
    query = f"SELECT {distinct_select} FROM ({base_query})"
    data, _ = query_athena(database="run_eval_db", query=query)
    distinct_dict = data.to_dict("list")
    return distinct_dict


def get_best_fb_per_net(nets):
    if not nets["gt_tables"] or not nets["pred_tables"]:
        return None

    query = generate_fb_query(
        nets["gt_tables"],
        nets["pred_tables"],
        nets["meta_data"],
    )
    data, _ = query_athena(database="run_eval_db", query=query)
    data = data.fillna(1)
    net_id_to_best_thresh = calc_best_thresh(data)
    return net_id_to_best_thresh


def get_list_of_scene_signals(nets):
    if not nets["frame_tables"]:
        return None

    cols_query = generate_cols_query(nets["frame_tables"], search_string="scene_signals_")
    cols_data, _ = query_athena(database="run_eval_db", query=cols_query)
    if cols_data.empty:
        return None
    cols_mest_names = set.intersection(
        *[
            set(
                name.replace("scene_signals_", "").replace("_mest_pred", "")
                for name in cols_data[cols_data["TABLE_NAME"] == table_name]["COLUMN_NAME"]
                if name.endswith("_mest_pred")
            )
            for table_name in cols_data["TABLE_NAME"]
        ]
    )
    cols_pred_names = set.intersection(
        *[
            set(
                name.replace("scene_signals_", "").replace("_pred", "")
                for name in cols_data[cols_data["TABLE_NAME"] == table_name]["COLUMN_NAME"]
                if not name.endswith("_mest_pred") and name.endswith("_pred")
            )
            for table_name in cols_data["TABLE_NAME"]
        ]
    )
    list_of_scene_signals = {"pred": sorted(cols_pred_names), "mest": sorted(cols_mest_names)}
    return list_of_scene_signals
