import re
from dataclasses import dataclass, field
from itertools import zip_longest
from threading import Thread
from queue import Queue

from road_database_toolkit.athena.athena_utils import query_athena


@dataclass
class Table:
    name: str
    tables_dict: dict
    columns_to_type: dict = field(default_factory=dict)
    columns_distinguish_values: dict = field(default_factory=dict)
    columns_options: list = field(default_factory=list)


class Tables:
    def __init__(self, dump_names, **kwargs):
        self.names = dump_names

        general_meta_data_tables = kwargs.get("meta_data_table", [])

        lm_meta_data_tables = kwargs.get("lm_meta_data_table", [""] * len(general_meta_data_tables))
        lm_meta_data_tables = self.replace_nones(lm_meta_data_tables)

        re_meta_data_tables = kwargs.get("re_meta_data_table", [""] * len(general_meta_data_tables))
        re_meta_data_tables = self.replace_nones(re_meta_data_tables)

        pw_meta_data_tables = kwargs.get("pw_meta_data_table", [""] * len(general_meta_data_tables))
        pw_meta_data_tables = self.replace_nones(pw_meta_data_tables)

        q1, q2, q3, q4 = Queue(), Queue(), Queue(), Queue()
        Thread(
            target=wrapper, args=(generate_table_instance, q1, "meta_data", general_meta_data_tables, dump_names)
        ).start()
        Thread(
            target=wrapper, args=(generate_table_instance, q2, "lm_meta_data", lm_meta_data_tables, dump_names)
        ).start()
        Thread(
            target=wrapper, args=(generate_table_instance, q3, "re_meta_data", re_meta_data_tables, dump_names)
        ).start()
        Thread(
            target=wrapper, args=(generate_table_instance, q4, "pw_meta_data", pw_meta_data_tables, dump_names)
        ).start()

        self.meta_data = q1.get()
        self.lm_meta_data = q2.get()
        self.re_meta_data = q3.get()
        self.pw_meta_data = q4.get()

    @staticmethod
    def replace_nones(tables_list):
        return [table if table else "" for table in tables_list]


def wrapper(func, queue, *args):
    queue.put(func(*args))


def generate_table_instance(name, tables, dump_names):
    table = tables[0]
    tables_dict = dict(zip_longest(dump_names, tables))
    if not table:
        return Table(name, tables_dict)

    columns_type = get_columns_data_types(table)

    uninteresting_columns = [
        "s3_path",
        "pred_name",
        "dump_name",
        "population",
        "grabindex",
    ]
    relevant_columns_type = {
        col: dtype
        for col, dtype in columns_type.items()
        if col not in uninteresting_columns and not re.search(r"(_|.)\d+$", col)
    }

    columns_options = parse_columns_options(relevant_columns_type)
    columns_distinguish_values = generate_meta_data_dicts(table, relevant_columns_type)

    table_data = Table(name, tables_dict, columns_type, columns_distinguish_values, columns_options)
    return table_data


def get_columns_data_types(table):
    query = f"SELECT * FROM ({table}) LIMIT 1"
    data, _ = query_athena(database="run_eval_db", query=query)
    columns_type = {k.lower(): v for k, v in data.dtypes.apply(lambda x: x.name).to_dict().items()}
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
