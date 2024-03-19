import re
import pandas as pd
from road_database_toolkit.athena.athena_utils import query_athena
from road_database_toolkit.dynamo_db.db_manager import DBManager

from road_dump_dashboard.components.dump_properties import Dumps


run_eval_db_manager = DBManager(table_name="algoroad_dump_catalog", primary_key="dump_name")


def init_dumps(rows):
    dumps = Dumps(
        rows["dump_name"],
        **{table: rows[table].tolist() for table in rows.columns if table.endswith("_table") and any(rows[table])},
    ).__dict__
    return dumps


def parse_catalog_rows(rows, derived_virtual_selected_rows):
    rows = pd.DataFrame([rows[i] for i in derived_virtual_selected_rows])
    return rows


def generate_meta_data_dicts(md_table):
    md_columns_to_type = get_meta_data_columns(md_table)
    md_columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in md_columns_to_type.keys()]

    distinct_dict = get_distinct_values_dict(md_table, md_columns_to_type)

    DISTINCT_LIMIT = 50
    md_columns_to_distinguish_values = {
        col: [{"label": val.strip(" "), "value": f"'{val.strip(' ')}'"} for val in val_list[0].strip("[]").split(",")[:DISTINCT_LIMIT]]
        for col, val_list in distinct_dict.items()
    }

    return md_columns_to_type, md_columns_options, md_columns_to_distinguish_values


def get_meta_data_columns(md_table):
    query = f"SELECT * FROM ({md_table}) LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    sub_columns = list(col for col in data.columns if re.search(r'_\d+$', col))
    uninteresting_columns = ['s3_path', 'pred_name', 'dump_name', 'population']
    data = data.drop(uninteresting_columns + sub_columns, axis=1, errors='ignore')
    md_columns_to_type = dict(data.dtypes.apply(lambda x: x.name))
    return md_columns_to_type


def get_distinct_values_dict(md_table, md_columns_to_type):
    distinct_select = ",".join(
        [
            f' array_agg(DISTINCT "{col}") AS "{col}" '
            for col in md_columns_to_type.keys()
            if md_columns_to_type[col] == "object"
        ]
    )
    query = f"SELECT {distinct_select} FROM ({md_table})"
    data, _ = query_athena(database="run_eval_db", query=query)
    distinct_dict = data.to_dict("list")
    return distinct_dict
