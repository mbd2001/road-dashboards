from road_database_toolkit.athena.athena_utils import query_athena

from road_dashboards.road_eval_dashboard.components.common_filters import ALL_FILTERS
from road_dashboards.road_eval_dashboard.components.queries_manager import (
    generate_base_query,
    generate_grab_index_hist_query,
)


def generate_meta_data_dicts(nets):
    md_columns_to_type = get_meta_data_columns(nets)
    distinct_dict = get_distinct_values_dict(nets, md_columns_to_type)

    md_columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in md_columns_to_type.keys()]
    md_columns_to_distinguish_values = {
        col: [{"label": val.strip(" "), "value": f"'{val.strip(' ')}'"} for val in val_list[0].strip("[]").split(",")]
        for col, val_list in distinct_dict.items()
    }
    return md_columns_to_type, md_columns_options, md_columns_to_distinguish_values


def generate_effective_samples_per_filter(nets):
    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    query = generate_grab_index_hist_query(tables_lists, meta_data, ALL_FILTERS)
    try:
        data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=60 * 24 * 3)
        effective_samples_per_batch = data.to_dict("records")[0]
        return effective_samples_per_batch
    except:
        print("Failed to compute num of effective samples per filter. Some of the filters might not exist in the data?")
        return {}


def get_meta_data_columns(nets):
    query = f"SELECT * FROM {nets['meta_data']} LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=60 * 24 * 3)
    md_columns_to_type = dict(data.dtypes.apply(lambda x: x.name))
    return md_columns_to_type


def get_distinct_values_dict(nets, md_columns_to_type, max_distinct_values=30):
    distinct_select = ",".join(
        [
            f' slice(array_agg(DISTINCT "{col}"), 1, {max_distinct_values}) AS "{col}" '
            for col in md_columns_to_type.keys()
            if md_columns_to_type[col] == "object"
        ]
    )
    if not distinct_select:
        return {}

    tables_lists = nets["frame_tables"]
    meta_data = nets["meta_data"]
    base_query = generate_base_query(tables_lists, meta_data)
    query = f"SELECT {distinct_select} FROM ({base_query})"
    data, _ = query_athena(database="run_eval_db", query=query, cache_duration_minutes=60 * 24 * 3)
    distinct_dict = data.to_dict("list")
    return distinct_dict
