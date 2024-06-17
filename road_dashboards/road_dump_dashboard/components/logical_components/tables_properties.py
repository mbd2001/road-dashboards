import re
from dataclasses import dataclass, field
from itertools import zip_longest
from queue import Queue
from threading import Thread

from road_database_toolkit.athena.athena_utils import query_athena

POSITION_COLUMNS = [
    "half_width",
    "pos",
    "pos_X",
    "pos_Z",
    "ds_y_off",
    "de_y_off",
    "dp_points",
    "dv_dp_points",
]


@dataclass
class Table:
    name: str
    tables_dict: dict
    columns_to_type: dict = field(default_factory=dict)
    columns_distinguish_values: dict = field(default_factory=dict)
    columns_options: list = field(default_factory=list)


class Tables:
    POTENTIAL_TABLES = ["meta_data", "lm_meta_data", "re_meta_data", "pw_meta_data", "rpw_meta_data"]

    def __init__(self, dump_names, **kwargs):
        self.names = dump_names
        self.meta_data, self.lm_meta_data, self.re_meta_data, self.pw_meta_data, self.rpw_meta_data = self.init_tables(
            dump_names, **kwargs
        )

    @staticmethod
    def get_tables_from_type(tables_type, num_of_dumps, **kwargs):
        tables = kwargs.get(f"{tables_type}_table", [""] * num_of_dumps)
        tables = [table if table else "" for table in tables]
        return tables

    def init_tables(self, dump_names, **kwargs):
        num_of_dumps = len(kwargs.get("meta_data_table"))
        tables_list = [
            self.get_tables_from_type(table_type, num_of_dumps, **kwargs) for table_type in self.POTENTIAL_TABLES
        ]
        queues = [Queue() for _ in self.POTENTIAL_TABLES]
        [
            Thread(target=wrapper, args=(generate_table_instance, queue, table_type, tables, dump_names)).start()
            for queue, table_type, tables in zip(queues, self.POTENTIAL_TABLES, tables_list)
        ]
        table_instances = [queue.get() for queue in queues]
        return table_instances


def wrapper(func, queue, *args):
    queue.put(func(*args))


def generate_table_instance(name, tables, dump_names):
    table = tables[0]
    tables_dict = dict(zip_longest(dump_names, tables))
    if not table:
        return Table(name, tables_dict)

    columns_type = get_columns_data_types(table)
    relevant_columns_type = {
        col: dtype
        for col, dtype in columns_type.items()
        if not any(col.startswith(pos_col) for pos_col in POSITION_COLUMNS)
    }

    columns_options = parse_columns_options(relevant_columns_type)
    columns_distinguish_values = generate_meta_data_dicts(table, relevant_columns_type)

    table_data = Table(name, tables_dict, columns_type, columns_distinguish_values, columns_options)
    return table_data


def get_columns_data_types(table):
    uninteresting_columns = [
        "s3_path",
        "pred_name",
        "dump_name",
        "population",
    ]

    query = f"SELECT * FROM ({table}) LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    columns_type = {
        k.lower(): v for k, v in data.dtypes.apply(lambda x: x.name).to_dict().items() if k not in uninteresting_columns
    }
    return columns_type


def generate_meta_data_dicts(table, columns_data_types_list):
    distinct_dict = get_distinct_values_dict(table, columns_data_types_list)
    columns_distinguish_values = parse_distinct_dict(distinct_dict)
    return columns_distinguish_values


def get_distinct_values_dict(table, columns_data_types_list):
    distinct_select = ",".join(
        [
            f' array_agg(DISTINCT "{col}") AS "{col}" '
            for col, dtype in columns_data_types_list.items()
            if dtype == "object"
        ]
    )
    if not distinct_select:
        return {}

    query = f"SELECT {distinct_select} FROM {table}"
    data, _ = query_athena(database="run_eval_db", query=query)
    distinct_dict = data.to_dict("list")
    return distinct_dict


def parse_distinct_dict(distinct_dict, max_distinct_values=30):
    columns_to_distinguish_values = {
        col: [
            {"label": val.strip(" "), "value": f"'{val.strip(' ')}'"}
            for val in val_list[0].strip("[]").split(",")[:max_distinct_values]
        ]
        for col, val_list in distinct_dict.items()
    }
    return columns_to_distinguish_values


def parse_columns_options(columns_to_type):
    columns_options = [{"label": col.replace("_", " ").title(), "value": col} for col in columns_to_type.keys()]
    return columns_options


def get_value_from_tables_property_union(
    key, main_tables, meta_data_tables=None, prop="columns_to_type", key_as_prefix=False
):
    val = main_tables[prop].get(key)
    if val is None and meta_data_tables is not None:
        val = meta_data_tables[prop].get(key)
    if val is not None or key_as_prefix is False:
        return val

    union_dicts = get_tables_property_union(main_tables, meta_data_tables, prop)
    for dict_key, dict_val in union_dicts.items():
        if dict_key.startswith(key):
            return dict_val
    return None


def get_tables_property_union(main_tables, meta_data_tables=None, prop="columns_options"):
    main_dict = main_tables[prop]
    meta_data_dict = meta_data_tables[prop] if meta_data_tables else None
    if isinstance(main_dict, list):
        return main_dict + (meta_data_dict if meta_data_dict is not None else [])
    return {**main_dict, **(meta_data_dict if meta_data_dict is not None else {})}
